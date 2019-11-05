#
import json
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit, QFileDialog
import vtk
import numpy as np
import math
import os
from lxml import etree
from standardWidgets import ak3LoadButton, removeButton, editButton, setupWindow, messageboxOK, progressWindow
from loads import load

# tbl load
class tbl(load):
    def __init__(self, ak3path, myModel, vtkWindow):
        super(tbl, self).__init__()
        self.ak3path = ak3path
        self.myModel = myModel
        self.removeButton = removeButton(self.ak3path)
        self.editButton = editButton()
        self.type = 'Turbulent_Boundary_Layer'
        #
        self.dirX = QLineEdit('0.')
        self.dirY = QLineEdit('0.')
        self.dirZ = QLineEdit('1.')
        self.flowDirX = QLineEdit('1.')
        self.flowDirY = QLineEdit('0.')
        self.flowDirZ = QLineEdit('0.')
        self.loadButton = ak3LoadButton(self.ak3path)
        self.loadButton.clicked.connect(self.getFilename)
        self.dataPoints = []
        #
        self.label = QLabel('Turbulent Boundary Layer')
        self.dirLabel = QLabel('x ' + self.flowDirX.text() + ' y ' + self.flowDirY.text() + ' z ' + self.flowDirZ.text())
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.dirLabel, self.drawCheck, self.editButton]]
        #
        self.initSetupWindow()
        self.init3DActor(vtkWindow)
        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        #
        self.editButton.clicked.connect(self.showEdit)
        var = self.showEdit()
        if var == 0: # is the case if the initial setup window is canceled by the user
            self.generatePressure()
            self.update3DActor()
    #
    def calcCorcosIntensity(self, kX, kY, omega, uC, alphaX = 0.1, alphaY = 0.77):
        P1 = 4.*alphaX*alphaY
        P2 = alphaY**2. + (kY*uC/omega)**2.
        P3 = alphaX**2. + (kX*uC/omega - 1.)**2.
        spectrumFactor = (uC/omega)**2. / (2.*math.pi)**2.
        return spectrumFactor*P1/(P2*P3)
    #
    def clearLayout(self):
        """
        Clear all content in planeWave layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))
    #
    def generatePressure(self):
        """
        Calculates pressure excitation on the selected blocks according to Klabes 2017 (autospectrum) and Efimtsov (Wavenumber-spectrum) due to a turbulent boundary layer
        """
        frequencies = self.myModel.calculationObjects[0].frequencies
        self.findRelevantPoints()
        if self.surfacePoints is not []:
            self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
            self.surfaceAmps = np.zeros((len(frequencies),len(self.surfacePoints)))
            if self.dataPoints==[]: 
                msg = messageboxOK('Error', 'No parameter input file loaded.\nNo calculation possible!\n')
            else:
                self.nearestNeighbor()
                r_vector = []
                # Get model infos
                nodes = self.myModel.calculationObjects[0].nodes
                center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
                flowDir = [float(self.flowDirX.text()), float(self.flowDirY.text()), float(self.flowDirZ.text())]
                flowDir = flowDir/np.linalg.norm(flowDir)
                # Calculate distances in direction of the flow
                progWin = progressWindow(len(self.surfacePoints)-1, "Calculating TBL load")
                for nsp, surfacePoint in enumerate(self.surfacePoints):
                    r_vector.append(abs(flowDir[0]*(surfacePoint[0] - center[0]) + flowDir[1]*(surfacePoint[1] - center[1]) + flowDir[2]*(surfacePoint[2] - center[2])))
                    # Calculate: AMPS according to Klabes 2017 ; PHASES using Efimtsov model 
                    idx = self.euclNearest[nsp] # index of dataPoint (loaded before via json file) which is nearest to current surfacePoint
                    a = self.par_a[idx]
                    b = self.par_b[idx]
                    c = self.par_c[idx]
                    d = self.par_d[idx]
                    e = self.par_e[idx]
                    f = self.par_f[idx]
                    g = self.par_g[idx]
                    h = self.par_h[idx]
                    delta = self.par_delta[idx]
                    uC = self.par_uC[idx]
                    uE = self.par_uE[idx]
                    uTau = self.par_uTau[idx]
                    tauW = self.par_tauW[idx]
                    nu = self.par_nu[idx]
                    #
                    for nf, freq in enumerate(frequencies):
                        omega = 2.*math.pi*freq
                        # Goody 2004 / Klabes 2017
                        Rt = (delta/uE)/(nu/uTau**2.)
                        scalingFactor = ((tauW**2.)*delta)/uE
                        P0 = 2.*math.pi*freq*delta/uE
                        P1 = a*P0**b
                        P2 = (P0**c + d)**e
                        P3 = (f*(Rt**g)*P0)**h
                        phi = scalingFactor*P1/(P2 + P3)
                        self.surfaceAmps[nf,nsp] = phi**0.5
                        # Corcos
                        kC = omega/uC
                        steps = 10
                        dK = 20*kC/(steps-1)
                        kRange = np.linspace(-10*kC,10*kC,steps)[:-1] + dK/2. # Midpoint in discrete intervals
                        dens = []
                        for kX in kRange:
                            for kY in kRange:
                                dens.append(self.calcCorcosIntensity(kX, kY, omega, uC))
                        #print(np.sum(dens)*dK**2.)
                        self.surfacePhases[nf,nsp] = 1.
                        #
                        progWin.setValue(nsp)
                        QApplication.processEvents()
    #
    def getFilename(self):
        """
        Open menu to choose file which contains point data for tbl parameters
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(None,"QFileDialog.getOpenFileName()", "","All Files (*);;json Files (*.json)", options=options)
        if fileName:
            self.filename = fileName
        datanew = self.loadData(fileName) #calls loadData function to read the file
    #
    def getXYdata(self):
        """
        Return x, y data for plotting; for tbl load: mean amplitude per frequency
        """
        return self.myModel.calculationObjects[0].frequencies, np.mean(self.surfaceAmps, axis=1)
    #
    def init3DActor(self, vtkWindow):
        """
        initialize vtk objects
        """
        # Get model infos
        nodes = self.myModel.calculationObjects[0].nodes
        center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        flowDir = [float(self.flowDirX.text()), float(self.flowDirY.text()), float(self.flowDirZ.text())]
        flowDir = flowDir/np.linalg.norm(flowDir)
        scaleFactor = max( [abs(max(nodes[:,1])-min(nodes[:,1])), abs(max(nodes[:,2])-min(nodes[:,2])), abs(max(nodes[:,3])-min(nodes[:,3]))] )
        # Symbol for normal direction of load
        # Calculate random directions in the plane
        direction1 = np.cross(loadNormal, [loadNormal[0]+0.11*loadNormal[1], loadNormal[1]+0.22*loadNormal[2], loadNormal[2]+0.33*loadNormal[0]])
        direction1 = direction1/np.linalg.norm(direction1)
        direction2 = np.cross(loadNormal, direction1)
        direction2 = direction2/np.linalg.norm(direction2)
        # Create vtk quad object
        self.loadGridSymbol = vtk.vtkUnstructuredGrid()
        vtkPoints = vtk.vtkPoints()
        [vtkPoints.InsertNextPoint(center[0] + scaleFactor*loadNormal[0] + scaleFactor*0.2*edge[0], center[1] + scaleFactor*loadNormal[1] + scaleFactor*0.2*edge[1], center[2] + scaleFactor*loadNormal[2] + scaleFactor*0.2*edge[2]) for edge in [-direction1-direction2, -direction1+direction2, direction1+direction2, direction1-direction2]]
        self.loadGridSymbol.SetPoints(vtkPoints)
        quad_ = vtk.vtkQuad()
        [quad_.GetPointIds().SetId(p, p) for p in range(4)] # Set four nodes
        self.loadGridSymbol.InsertNextCell(quad_.GetCellType(), quad_.GetPointIds())
        # Create mapper and actor
        self.loadMapperSymbol = vtk.vtkDataSetMapper()
        self.loadMapperSymbol.SetInputData(self.loadGridSymbol)
        self.loadActorSymbol = vtk.vtkActor()
        self.loadActorSymbol.SetMapper(self.loadMapperSymbol)
        self.loadActorSymbol.GetProperty().SetColor(1., 0.6, 0.)
        self.loadActorSymbol.GetProperty().SetAmbient(0.9);
        self.loadActorSymbol.GetProperty().SetDiffuse(0.1);
        self.loadActorSymbol.GetProperty().SetSpecular(0.);
        # Arrow for normal direction of load and flow direction (3 arrows)
        self.arrowDataSymbol = vtk.vtkPolyData()
        arrowPointsSymbol = vtk.vtkPoints()
        arrowPointsSymbol.InsertNextPoint(center[0] + scaleFactor*loadNormal[0], center[1] + scaleFactor*loadNormal[1], center[2] + scaleFactor*loadNormal[2])
        arrowPointsSymbol.InsertNextPoint(center[0] + scaleFactor*flowDir[0],    center[1] + scaleFactor*flowDir[1],    center[2] + scaleFactor*flowDir[2])
        self.arrowDataSymbol.SetPoints(arrowPointsSymbol)
        self.arrowVectorsSymbol = vtk.vtkDoubleArray()
        self.arrowVectorsSymbol.SetNumberOfComponents(3)
        self.arrowVectorsSymbol.InsertNextTuple([scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
        self.arrowVectorsSymbol.InsertNextTuple([scaleFactor*-0.2*flowDir[0],    scaleFactor*-0.2*flowDir[1],    scaleFactor*-0.2*flowDir[2]])
        self.arrowDataSymbol.GetPointData().SetVectors(self.arrowVectorsSymbol)
        arrowSource = vtk.vtkArrowSource()
        # Glyph for load symbol
        glyphSymbol = vtk.vtkGlyph3D()
        glyphSymbol.SetScaleModeToScaleByVector()
        glyphSymbol.SetSourceConnection(arrowSource.GetOutputPort())
        glyphSymbol.SetInputData(self.arrowDataSymbol)
        glyphSymbol.Update()
        # Mapper for load symbol
        self.arrowMapperSymbol = vtk.vtkPolyDataMapper()
        self.arrowMapperSymbol.SetInputConnection(glyphSymbol.GetOutputPort())
        # Actor for load symbol
        self.arrowActorSymbol = vtk.vtkActor()
        self.arrowActorSymbol.GetProperty().SetColor(1., 0.6, 0.)
        self.arrowActorSymbol.SetMapper(self.arrowMapperSymbol)
        # Arrows for load application
        self.arrowDataLoad = vtk.vtkPolyData()
        arrowPointLoad = vtk.vtkPoints()
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        # Glyph for load symbol
        glyphLoad = vtk.vtkGlyph3D()
        glyphLoad.SetScaleModeToScaleByVector()
        glyphLoad.SetSourceConnection(arrowSource.GetOutputPort())
        glyphLoad.SetInputData(self.arrowDataLoad)
        glyphLoad.Update()
        # Mapper for load
        self.arrowMapperLoad = vtk.vtkPolyDataMapper()
        self.arrowMapperLoad.SetInputConnection(glyphLoad.GetOutputPort())
        # Actor for load
        self.arrowActorLoad = vtk.vtkActor()
        self.arrowActorLoad.GetProperty().SetColor(1., 0.6, 0.)
        self.arrowActorLoad.SetMapper(self.arrowMapperLoad)

        #List of Actors for iteration in vtkWindow
        self.actorsList = [self.arrowActorLoad, self.arrowActorSymbol, self.loadActorSymbol]
    #
    def initSetupWindow(self):
        """
        basic objects for the individual setup window
        """
        self.setupWindow = setupWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Norm-Direction X'), self.dirX)
        self.setupWindow.layout.addRow(QLabel('Norm-Direction Y'), self.dirY)
        self.setupWindow.layout.addRow(QLabel('Norm-Direction Z'), self.dirZ)
        self.setupWindow.layout.addRow(QLabel('Flow-direction X'), self.flowDirX)
        self.setupWindow.layout.addRow(QLabel('Flow-direction Y'), self.flowDirY)
        self.setupWindow.layout.addRow(QLabel('Flow-direction Z'), self.flowDirZ)
        self.setupWindow.layout.addRow(QLabel('Load xyz input file'), self.loadButton)
        #
        self.blockChecker = []
        for block in self.myModel.calculationObjects[0].elems:
            self.blockChecker.append(QCheckBox())
            self.setupWindow.blockLayout.addRow(self.blockChecker[-1], QLabel('Block ' + str(block[1]) + ' (' + str(block[0]) + ')'))
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())
    #
    def loadData(self, filename):
        """
        Loads file with x,y,z flow data for Klabes and Efimstov parameter.
        Must be .json and must be a dict like: 
        {"pointdata":[
            {"coord":[0.0,1.7,0.0],"a":3.0,"b":2.0,"c":0.75,"d":0.5,"e":3.7,"f":1.1,"g":-0.57,"h":7.0,"delta":0.3,"uC":164.4,"uE":274.0,"uTau":7.0,"tauW":102.2,"nu":3.3e-5},
            {"coord":[0.2,1.7,0.0],"a":3.0,"b":2.0,"c":0.75,"d":0.5,"e":3.7,"f":1.1,"g":-0.57,"h":7.0,"delta":0.3,"uC":164.4,"uE":274.0,"uTau":7.0,"tauW":102.2,"nu":3.3e-5}
        ]}
        """
        with open(filename) as f:
            ld = json.load(f)
        #
        self.dataPoints = []
        #
        self.par_a = []
        self.par_b = []
        self.par_c = []
        self.par_d = []
        self.par_e = []
        self.par_f = []
        self.par_g = []
        self.par_h = []
        self.par_delta = []
        self.par_uC = []
        self.par_uE = []
        self.par_uTau = []
        self.par_tauW = []
        self.par_nu = []
        #
        for point in ld.get('pointdata'): 
            self.dataPoints.append(point.get('coord'))
            self.par_a.append(float(point.get('a')))
            self.par_b.append(float(point.get('b')))
            self.par_c.append(float(point.get('c')))
            self.par_d.append(float(point.get('d')))
            self.par_e.append(float(point.get('e')))
            self.par_f.append(float(point.get('f')))
            self.par_g.append(float(point.get('g')))
            self.par_h.append(float(point.get('h')))
            self.par_delta.append(float(point.get('delta')))
            self.par_uC.append(float(point.get('uC')))
            self.par_uE.append(float(point.get('uE')))
            self.par_uTau.append(float(point.get('uTau')))
            self.par_tauW.append(float(point.get('tauW')))
            self.par_nu.append(float(point.get('nu')))
    #
    def nearestNeighbor(self):
        """
        finds next elements to given data points, writes into a proximity list, which can then be applied to the elements list
        """
        self.euclNearest = []
        for m, surfPoint in enumerate(np.array(self.surfacePoints)):
            # Calculates dist to each loaded dataPoint and saves the index of the  nearest dataPoint
            self.euclNearest.append(np.argmin([np.sum(np.square(dataPoint - surfPoint)) for n, dataPoint in enumerate(np.array(self.dataPoints))]))
    #
    def resetValues(self):
        for n, item in enumerate([self.dirX, self.dirY, self.dirZ, self.flowDirX, self.flowDirY, self.flowDirZ]):
            item.setText(self.varSave[n])
    #
    def showEdit(self):
        self.varSave = [self.dirX.text(), self.dirY.text(), self.dirZ.text(), self.flowDirX.text(), self.flowDirY.text(), self.flowDirZ.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                if float(self.dirX.text()) == 0. and float(self.dirY.text()) == 0. and float(self.dirZ.text()) == 0.:
                    raise Exception
                if float(self.flowDirX.text()) == 0. and float(self.flowDirY.text()) == 0. and float(self.flowDirZ.text()) == 0.:
                    raise Exception
                self.dirLabel.setText('x ' + self.flowDirX.text() + ' y ' + self.flowDirY.text() + ' z ' + self.flowDirZ.text())
                self.generatePressure()
                self.update3DActor()
                self.switch()
            except: # if input is wrong, show message and reset values
                messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                self.resetValues()
        else:
            self.resetValues()
        return var

    # Method changing the objects changedSwitch in order to indicate 2D and 3D update
    def switch(self):
        if self.changeSwitch.isChecked():
            self.changeSwitch.setChecked(0)
        else:
            self.changeSwitch.setChecked(1)
    #
    def update3DActor(self):
        # Get model infos
        nodes = self.myModel.calculationObjects[0].nodes
        center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        flowDir = [float(self.flowDirX.text()), float(self.flowDirY.text()), float(self.flowDirZ.text())]
        flowDir = flowDir/np.linalg.norm(flowDir)
        scaleFactor = max( [abs(max(nodes[:,1])-min(nodes[:,1])), abs(max(nodes[:,2])-min(nodes[:,2])), abs(max(nodes[:,3])-min(nodes[:,3]))] )
        # Symbol for plane wave
        # Calculate random directions in the plane
        direction1 = np.cross(loadNormal, [loadNormal[0]+0.11*loadNormal[1], loadNormal[1]+0.22*loadNormal[2], loadNormal[2]+0.33*loadNormal[0]])
        direction1 = direction1/np.linalg.norm(direction1)
        direction2 = np.cross(loadNormal, direction1)
        direction2 = direction2/np.linalg.norm(direction2)
        # Update points of vtk quad object
        [self.loadGridSymbol.GetPoints().SetPoint(p, [center[0] + scaleFactor*loadNormal[0] + scaleFactor*0.2*edge[0], center[1] + scaleFactor*loadNormal[1] + scaleFactor*0.2*edge[1], center[2] + scaleFactor*loadNormal[2] + scaleFactor*0.2*edge[2]]) for p, edge in enumerate([-direction1-direction2, -direction1+direction2, direction1+direction2, direction1-direction2])]
        self.loadGridSymbol.GetPoints().Modified()
        # Update load symbol
        self.arrowDataSymbol.GetPoints().SetPoint(0, center[0] + scaleFactor*loadNormal[0], center[1] + scaleFactor*loadNormal[1], center[2] + scaleFactor*loadNormal[2])
        self.arrowDataSymbol.GetPoints().SetPoint(1, center[0] + scaleFactor*flowDir[0],    center[1] + scaleFactor*flowDir[1],    center[2] + scaleFactor*flowDir[2])
        self.arrowDataSymbol.GetPoints().Modified()
        self.arrowVectorsSymbol.SetTuple(0, [scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
        self.arrowVectorsSymbol.SetTuple(1, [scaleFactor*-0.2*flowDir[0],    scaleFactor*-0.2*flowDir[1],    scaleFactor*-0.2*flowDir[2]])
        self.arrowVectorsSymbol.Modified()
        # Update load
        arrowPointLoad = vtk.vtkPoints()
        [arrowPointLoad.InsertNextPoint([point[0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], point[1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], point[2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p, point in enumerate(self.surfacePoints)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.1*scaleFactor*vec[0], -0.1*scaleFactor*vec[1], -0.1*scaleFactor*vec[2]]) for vec in self.surfaceElementNormals]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()
    #
    def writeXML(self, exportAK3, name):
        elemLoads = exportAK3.find('ElemLoads')
        oldNoOfLoads = elemLoads.get('N')
        elemLoads.set('N', str(int(oldNoOfLoads) + len(self.surfaceElements)))
        loadedElems = exportAK3.find('LoadedElems')
        # Create a directory for load dat files
        loadDir = '/'.join(self.myModel.path.split('/')[0:-1]) + '/' + name + '_' + self.type + '_load_' + str(self.removeButton.id+1)
        if not os.path.exists(loadDir):
            os.mkdir(loadDir)
        else: # Clean directory
            for filename in os.listdir(loadDir):
                os.remove(loadDir + '/' + filename)
        # Save loads for each element
        progWin = progressWindow(len(self.surfaceElements)-1, 'Exporting ' + self.type + ' load ' + str(self.removeButton.id+1))
        for nE, surfaceElem in enumerate(self.surfaceElements):
            # One load per element
            newLoad = etree.Element('ElemLoad', Type='structurefrq')
            newLoad.tail = '\n'
            newLoadID = etree.Element('Id')
            newLoadID.text = str(self.removeButton.id+1) + str(surfaceElem) # The id is a concatanation by the load id and the elem id
            newLoad.append(newLoadID)
            newFile = etree.Element('File')
            newFile.text = '../' + name + '_' + self.type + '_load_' + str(self.removeButton.id+1) + '/elemLoad' + newLoadID.text + '.dat'
            newLoad.append(newFile)
            elemLoads.append(newLoad)
            # Save one file per load
            frequencies = self.myModel.calculationObjects[0].frequencies
            f = open(loadDir + '/elemLoad' + str(newLoadID.text) + '.dat', 'w')
            f.write(str(len(frequencies)) + '\n')
            [f.write(str(frequencies[nf]) + ' ' + str(-1.*float(self.surfaceAmps[nf,nE])*self.surfaceElementNormals[nE][0]) + ' ' + str(-1.*float(self.surfaceAmps[nf,nE])*self.surfaceElementNormals[nE][1]) + ' ' + str(-1.*float(self.surfaceAmps[nf,nE])*self.surfaceElementNormals[nE][2]) + ' ' + str(self.surfacePhases[nf,nE]) + '\n') for nf in range(len(frequencies))]
            f.close()
            # Apply load to element
            newLoadedElem = etree.Element('LoadedElem')
            newLoadedElem.tail = '\n'
            newElemID = etree.Element('Id')
            newElemID.text = str(surfaceElem) # Element ID
            newLoadedElem.append(newElemID)
            newLoadID = etree.Element('Load')
            newLoadID.text = str(self.removeButton.id+1) + str(surfaceElem) # Load ID
            newLoadedElem.append(newLoadID)
            loadedElems.append(newLoadedElem)
            # Update progress window
            progWin.setValue(nE)
            QApplication.processEvents()
