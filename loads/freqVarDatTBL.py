#
import json
from PyQt5.QtWidgets import QLabel, QWidgetItem, QCheckBox, QLineEdit, QFileDialog, QHBoxLayout
import vtk
import numpy as np
import h5py
import cmath
from standardWidgets import ak3LoadButton, removeButton, editButton, messageboxOK, setupLoadWindow
from standardFunctionsGeneral import isPlateType
from loads import elemLoad

# distributed time domain load
class freqVarDatTBL(elemLoad):
    """
    class for distributed time domain loads. Provides methods for loading, saving and processing data.
    """
    def __init__(self, myModel):
        """
        initialise basic load dependent GUI objects
        """
        super(freqVarDatTBL, self).__init__()
        self.myModel = myModel
        self.removeButton = removeButton()
        self.editButton = editButton()
        self.type = 'freqVarDat'
        #
        self.dirX = QLineEdit('0.')
        self.dirY = QLineEdit('1.')
        self.dirZ = QLineEdit('0.')
        #
        self.loadButton = ak3LoadButton()
        self.loadButton.clicked.connect(self.getFilename)
        self.dataPoints = []
        #
        self.label = QLabel('Distr. freq domain data TBL')
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.drawCheck, self.editButton]]
        #
        self.initSetupWindow()
        self.init3DActor()
        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        #
        self.editButton.clicked.connect(self.showEdit)
        var = self.showEdit()
        if var == 0: # is the case if the initial setup window is canceled by the user
            self.generatePressure()
            self.update3DActor()


    def clearLayout(self):
        """
        Clear all content in layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))


    def getFilename(self):
        """
        Open menu to choose file which contains point/time data
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(None,"QFileDialog.getOpenFileName()", "","All Files (*);;json Files (*.json)", options=options)
        if fileName:
          self.filename = fileName
          self.loadData(fileName) #calls loadData function to read the file

    def generatePressure(self):
        """
        combines nearest points and data: writes into a list of length of the element list
        """
        frequencies = self.myModel.frequencies
        print('Relevant points')
        self.findRelevantPoints()
        vec=[0,0,0]
        vec[0]=np.max(self.interpfield['X'])
        vec[1]=np.max(self.interpfield['Y'])
        vec[2]=np.max(self.interpfield['Z'])
        print(vec)
        plotIndexes=[2,1,0]
        if self.surfacePoints is not []:
                self.surfaceAmps = np.zeros((len(frequencies),len(self.surfacePoints)))
                self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
                for nsp, idx in enumerate(self.surfacePoints):
                    for nf, freq in enumerate(frequencies):
                        #myindx=np.where(self.interpfield['Frequency']==freq)
                        #myindx=myindx[0][0]
                        #self.surfaceAmps[nf,nsp] = np.abs(self.interpfield['PressuresInterpolations'][myindx](idx[plotIndexes[0]]+8.5,idx[plotIndexes[1]],idx[plotIndexes[2]]))
                        #phase = np.angle(self.interpfield['PressuresInterpolations'][myindx](idx[plotIndexes[0]]+8.5,idx[plotIndexes[1]],idx[plotIndexes[2]]))
                        #print(freq,idx[plotIndexes[0]]+8.5,idx[plotIndexes[1]],idx[plotIndexes[2]])
                        #input()
                        Pressures=self.interpfield['PressuresInterpolations'](idx[plotIndexes[0]]+8.5,idx[plotIndexes[1]],idx[plotIndexes[2]],freq)
                        self.surfaceAmps[nf,nsp]=np.abs(Pressures)
                        phase = np.angle(Pressures)
                        # Set range from 0 to 2pi
                        if phase<0.:
                            self.surfacePhases[nf,nsp] = 2*np.pi + phase
                        else:
                            self.surfacePhases[nf,nsp] = phase

    def getPhases(self):
        """
        calculates phases out of complex frequency domain data
        """
        self.surfacePhases = np.zeros((max(self.freqLenVec),len(self.surfacePoints)))
        for nf in range(max(self.freqLenVec)):
            for ne in range(len(self.surfacePoints)):
                if self.FreqData[ne] == 0:
                    self.surfacePhases[nf,ne] = 0
                else:
                    self.surfacePhases[nf,ne] = cmath.phase(self.FreqData[ne][nf])


    def getXYdata(self):
        """
        Returns x, y data for plotting
        """
        return self.myModel.frequencies, np.mean(self.surfaceAmps, axis=1), 'F-data'


    def init3DActor(self):
        """
        initialize vtk objects
        """
        # Get model infos
        nodes = self.myModel.nodes
        center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
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
        self.arrowActorLoad.GetProperty().SetColor(1., 0.4, 0.)
        self.arrowActorLoad.SetMapper(self.arrowMapperLoad)

        #List of Actors for iteration in vtkWindow
        self.actorsList = [self.arrowActorLoad, self.arrowActorSymbol, self.loadActorSymbol]

    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupLoadWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Norm-Direction X'), self.dirX)
        self.setupWindow.layout.addRow(QLabel('Norm-Direction Y'), self.dirY)
        self.setupWindow.layout.addRow(QLabel('Norm-Direction Z'), self.dirZ)
        self.setupWindow.layout.addRow(QLabel('Load time data input file'), self.loadButton)
        #
        self.blockChecker = []
        for block in self.myModel.elems:
            self.blockChecker.append(QCheckBox())
            if not isPlateType(str(block.attrs['ElementType'])):
                self.blockChecker[-1].setEnabled(False)
            subLayout = QHBoxLayout()
            [subLayout.addWidget(wid) for wid in [self.blockChecker[-1], QLabel('Block ' + str(block.attrs['Id']) + ' (' + str(block.attrs['ElementType']) + ')')]]
            subLayout.addStretch()
            self.setupWindow.blockLayout.addLayout(subLayout)
        self.setupWindow.blockLayout.addStretch()
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())

    #def loadDataOld(self, filename):
    #    """
    #    loads file with x,y,z data. must be .json and must be a dict like:
    #    {"pointdata":[
    #        {"coord":[0.0,1.7,0.0],"timedata":[0.0, 0.5407014555870047, -0.9596090131296847, 1.164619243635656]},
    #        {"coord":[0.2,1.7,0.0],"timedata":[-1.0813793556840758, 1.154942901919569, -0.9819364679621521]}
    #    """
    #    with open(filename) as f:
    #        ld = json.load(f)
    #    self.dataPoints = []
    #    self.timeValues = []
    #
    #    for point in ld.get('pointdata'):
    #        self.dataPoints.append(point.get('coord'))
    #        self.timeValues.append(point.get('timedata'))

    def loadData(self, filename):
        """
        Method to load time domain data from hdf5
        """
        self.interpfield = np.load(filename, allow_pickle=True).item()
        

    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate([self.dirX, self.dirY, self.dirZ]):
            item.setText(self.varSave[n])


    def showEdit(self):
        """
        recalculates data with new input parameters
        """
        self.varSave = [self.dirX.text(), self.dirY.text(), self.dirZ.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            if float(self.dirX.text()) == 0. and float(self.dirY.text()) == 0. and float(self.dirZ.text()) == 0.:
              raise Exception
            self.generatePressure()
            self.update3DActor()
            self.switch()
            #except: # if input is wrong, show message and reset values
                # messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                # self.resetValues()
        else:
            self.resetValues()
        return var


    def timeToFreq(self):
        """
        uses time data out of the loaded file to calculate a fft.
        """
        self.FreqValues = []
        self.freqLenVec = []
        self.AbsFreqValuesSq = []

        for nd, data in enumerate(self.timeValues):
            N=len(data)
            T=1/N
            Y = np.fft.fft(np.array(data))
            yf = 2.0/N * (Y[:N//2])
            self.FreqValues.append(yf.tolist())
            self.xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
            self.freqLenVec.append(len(self.xf))
            self.myModel.calculationObjects[0].frequencies = np.linspace(0.0, 1.0/(2.0*T), N/2, dtype=int)
            yfabsSq = np.square(np.abs((yf[:N//2])))
            self.AbsFreqValuesSq.append(yfabsSq.tolist())


    def update3DActor(self):
        """
        updates the vtk actors
        """
        # Get model infos
        nodes = self.myModel.nodes
        center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
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
