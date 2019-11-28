import json
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit, QFileDialog
import vtk
import numpy as np
import h5py
import cmath
import os
from lxml import etree
from standardWidgets import ak3LoadButton, removeButton, editButton, setupWindow, messageboxOK, progressWindow
from loads import load, loadInfoBox


class timeVarDat(load):
    """
    class for distributed time domain loads. Provides methods for loading, saving and processing data.
    """
    def __init__(self, ak3path, myModel, vtkWindow):
        """
        initialise basic load dependent GUI objects
        """
        super(timeVarDat, self).__init__()
        self.ak3path = ak3path
        self.myModel = myModel
        self.removeButton = removeButton(self.ak3path)
        self.editButton = editButton()
        self.type = 'timeVarDat'
        #
        self.amp = QLineEdit('1.')
        self.dirX = QLineEdit('0.')
        self.dirY = QLineEdit('0.')
        self.dirZ = QLineEdit('1.')
        self.ffttime = QLineEdit('1024')
        #
        self.loadButton = ak3LoadButton(self.ak3path)
        self.loadButton.clicked.connect(self.getFilename)
        self.dataPoints = []
        #
        self.label = QLabel('Distr. Time Domain')
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.drawCheck, self.editButton]]
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
            #self.generatePressure()
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
        datanew = self.loadData(fileName) #calls loadData function to read the file


    def generatePressure(self):
        """
        combines nearest points and data: writes into a list of length of the element list
        """
        frequencies = self.myModel.calculationObjects[0].frequencies
        self.findRelevantPoints()
        self.FreqData = [0 for x in self.surfacePoints]
        self.yfDataSq = [0 for x in self.surfacePoints]
        if self.surfacePoints is not []:
            self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
            if self.dataPoints==[]:
                msg = messageboxOK('Error', 'No parameter input file loaded.\nNo calculation possible!\n')
            else:
                self.nearestNeighbor()
                self.timeToFreq()

                i=0
                for x in self.euclNearest:
                    self.FreqData[i] = self.FreqValues[x]
                    self.yfDataSq[i] = self.AbsFreqValuesSq[x]
                    #self.surfaceAmps
                    i+=1

                self.getPhases()


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
        FreqArr = np.array(self.yfDataSq)
        yfMean = np.mean(FreqArr, axis=0)
        self.yfRootMean = np.sqrt(yfMean)

        if (len(self.myModel.calculationObjects[0].frequencies) == self.yfRootMean.size):
            return1 = self.myModel.calculationObjects[0].frequencies
            return2 = self.yfRootMean
        else:
            return1 = 0
            return2 = 0
            msg = messageboxOK('Error', 'Could not find data to print.\nNo visualisation possible!\n')
        return return1, return2


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


        arrowSource = vtk.vtkArrowSource()
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
        self.actorsList = [self.arrowActorLoad]


    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Sample Rate'), self.ffttime)
        self.setupWindow.layout.addWidget(self.loadButton)
        #
        self.blockChecker = []
        for block in self.myModel.calculationObjects[0].elems:
            self.blockChecker.append(QCheckBox())
            self.setupWindow.blockLayout.addRow(self.blockChecker[-1], QLabel('Block ' + str(block[1]) + ' (' + str(block[0]) + ')'))
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())


    def loadDataOld(self, filename):
        """
        loads file with x,y,z data. must be .json and must be a dict like:
        {"pointdata":[
            {"coord":[0.0,1.7,0.0],"timedata":[0.0, 0.5407014555870047, -0.9596090131296847, 1.164619243635656]},
            {"coord":[0.2,1.7,0.0],"timedata":[-1.0813793556840758, 1.154942901919569, -0.9819364679621521]}
        """
        with open(filename) as f:
            ld = json.load(f)
        self.dataPoints = []
        self.timeValues = []

        for point in ld.get('pointdata'):
            self.dataPoints.append(point.get('coord'))
            self.timeValues.append(point.get('timedata'))


    def loadData(self, filename):
        f = h5py.File(filename,'r')
        coord = f.get('ACoord')
        self.dataPoints = np.array(coord)
        data = f.get('AData')
        self.timeValues = np.array(data)
        self.dataPoints.tolist()
        self.timeValues.tolist()


    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate([self.ffttime]):
            item.setText(self.varSave[n])


    def showEdit(self):
        """
        recalculates data with new input parameters
        """
        self.varSave = [self.ffttime.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            #try:
            #if float(self.radius.text()) == 0. and float(self.samples.text()) == 0.:
                #raise Exception
            self.ffttime.setText(str(float(self.ffttime.text())))
            #c = float(self.c.text()) # It's just a check, variable is not used here
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
        nodes = self.myModel.calculationObjects[0].nodes
        center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:,1])-min(nodes[:,1])), abs(max(nodes[:,2])-min(nodes[:,2])), abs(max(nodes[:,3])-min(nodes[:,3]))] )

        # Update load
        arrowPointLoad = vtk.vtkPoints()

        ### get a lower number of arrows if there are more elements or the element size is small
        numberOfElem = len((self.myModel.calculationObjects[0].elems[0][2]))
        elemSize = abs(nodes[0,0] - nodes[1,0]) #only very rough
        elemDensity = numberOfElem / elemSize
        #print(self.myModel.calculationObjects[0].elems)
        print(nodes,elemSize)

        arrNoScale = int(numberOfElem/32)
        if arrNoScale<1:
            arrNoScale = 1
        ###
        [arrowPointLoad.InsertNextPoint([self.surfacePoints[p][0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], self.surfacePoints[p][1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], self.surfacePoints[p][2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p in range(0,len(self.surfacePoints),arrNoScale)]
        #[arrowPointLoad.InsertNextPoint([point[0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], point[1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], point[2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p, point in enumerate(self.surfacePoints)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.1*scaleFactor*vec[0], -0.1*scaleFactor*vec[1], -0.1*scaleFactor*vec[2]]) for vec in self.surfaceElementNormals]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()
