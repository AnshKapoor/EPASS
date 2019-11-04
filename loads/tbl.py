#
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit
import vtk
import numpy as np
import math
import os
from lxml import etree
from standardWidgets import removeButton, editButton, setupWindow, messageboxOK, progressWindow
from loads import load

# tbl load
class tbl(load):
    def __init__(self, ak3path, myModel, vtkWindow):
        super(tbl, self).__init__()
        self.ak3path = ak3path
        self.myModel = myModel
        self.removeButton = removeButton(self.ak3path)
        self.editButton = editButton()
        self.type = 'Turbulent Boundary Layer'
        #
        self.amp = QLineEdit('1.')
        self.dirX = QLineEdit('1.')
        self.dirY = QLineEdit('1.')
        self.dirZ = QLineEdit('1.')
        self.c = QLineEdit('340.')
        #
        self.label = QLabel('Turbulent Boundary Layer')
        self.ampLabel = QLabel(self.amp.text() + ' Pa')
        self.dirLabel = QLabel('x ' + self.dirX.text() + ' y ' + self.dirY.text() + ' z ' + self.dirZ.text())
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.ampLabel, self.dirLabel, self.drawCheck, self.editButton]]
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
        Calculates pressure excitation on the selected blocks due to the created plane wave
        """
        c = float(self.c.text())
        frequencies = self.myModel.calculationObjects[0].frequencies
        self.findRelevantPoints()
        #print(self.surfacePoints)
        if self.surfacePoints is not []:
            self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
            r_vector = []
             # Get model infos
            nodes = self.myModel.calculationObjects[0].nodes
            center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
            loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
            loadNormal = loadNormal/np.linalg.norm(loadNormal)
            # calculate distances in direction of the plane wave
            progWin = progressWindow(len(self.surfacePoints)-1, "Calculating distances")
            for nsp, surfacePoint in enumerate(self.surfacePoints):
                r_vector.append(abs(loadNormal[0]*(surfacePoint[0] - center[0]) + loadNormal[1]*(surfacePoint[1] - center[1]) + loadNormal[2]*(surfacePoint[2] - center[2])))
                progWin.setValue(nsp)
                QApplication.processEvents()
            # calculate the correct phases for the distances and apply the amp requested by the user in loadNormal direction to each element
            progWin = progressWindow(len(frequencies)-1, "Calculating phases")
            for nf, f in enumerate(frequencies):
                lam = c/f # wave length
                self.surfacePhases[nf,:] = [2*math.pi*(r % lam)/lam for r in r_vector]
                progWin.setValue(nf)
                QApplication.processEvents()

    #
    def getXYdata(self):
        """
        Return x, y data for plotting; for plane wave: constant amplitude
        """
        return self.myModel.calculationObjects[0].frequencies, len(self.myModel.calculationObjects[0].frequencies)*[float(self.amp.text())]

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
        scaleFactor = max( [abs(max(nodes[:,1])-min(nodes[:,1])), abs(max(nodes[:,2])-min(nodes[:,2])), abs(max(nodes[:,3])-min(nodes[:,3]))] )
        # Symbol for plane wave
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
        # Arrow for direction of load
        self.arrowDataSymbol = vtk.vtkPolyData()
        arrowPointsSymbol = vtk.vtkPoints()
        arrowPointsSymbol.InsertNextPoint(center[0] + scaleFactor*loadNormal[0], center[1] + scaleFactor*loadNormal[1], center[2] + scaleFactor*loadNormal[2])
        self.arrowDataSymbol.SetPoints(arrowPointsSymbol)
        self.arrowVectorsSymbol = vtk.vtkDoubleArray()
        self.arrowVectorsSymbol.SetNumberOfComponents(3)
        self.arrowVectorsSymbol.InsertNextTuple([scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
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





    def initSetupWindow(self):
        """
        basic objects for the individual setup window
        """
        self.setupWindow = setupWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Amplitude'), self.amp)
        self.setupWindow.layout.addRow(QLabel('Direction X'), self.dirX)
        self.setupWindow.layout.addRow(QLabel('Direction Y'), self.dirY)
        self.setupWindow.layout.addRow(QLabel('Direction Z'), self.dirZ)
        self.setupWindow.layout.addRow(QLabel('Speed of Sound'), self.c)
        #
        self.blockChecker = []
        for block in self.myModel.calculationObjects[0].elems:
            self.blockChecker.append(QCheckBox())
            self.setupWindow.blockLayout.addRow(self.blockChecker[-1], QLabel('Block ' + str(block[1]) + ' (' + str(block[0]) + ')'))
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())

    def resetValues(self):
        for n, item in enumerate([self.amp, self.dirX, self.dirY, self.dirZ, self.c]):
            item.setText(self.varSave[n])

    def showEdit(self):
        self.varSave = [self.amp.text(), self.dirX.text(), self.dirY.text(), self.dirZ.text(), self.c.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                if float(self.dirX.text()) == 0. and float(self.dirY.text()) == 0. and float(self.dirZ.text()) == 0.:
                    raise Exception
                self.ampLabel.setText(str(float(self.amp.text())) + ' Pa')
                self.dirLabel.setText('x ' + str(float(self.dirX.text())) + ' y ' + str(float(self.dirY.text())) + ' z ' + str(float(self.dirZ.text())))
                c = float(self.c.text()) # It's just a check, variable is not used here
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

    def update3DActor(self):
        # Get model infos
        nodes = self.myModel.calculationObjects[0].nodes
        center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
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
        self.arrowDataSymbol.GetPoints().Modified()
        self.arrowVectorsSymbol.SetTuple(0, [scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
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
            [f.write(str(frequencies[nf]) + ' ' + str(-1.*float(self.amp.text())*self.surfaceElementNormals[nE][0]) + ' ' + str(-1.*float(self.amp.text())*self.surfaceElementNormals[nE][1]) + ' ' + str(-1.*float(self.amp.text())*self.surfaceElementNormals[nE][2]) + ' ' + str(self.surfacePhases[nf,nE]) + '\n') for nf in range(len(frequencies))]
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
