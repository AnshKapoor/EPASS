import json
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit, QFileDialog
import vtk
import numpy as np
import math, cmath, random, time
import os
from lxml import etree
from standardWidgets import ak3LoadButton, removeButton, editButton, setupWindow, messageboxOK, progressWindow
from loads import load

import matplotlib.pyplot as plt



class timeVarDat(load):
    def __init__(self, ak3path, myModel, vtkWindow):
        super(timeVarDat, self).__init__()
        self.ak3path = ak3path
        self.myModel = myModel
        self.removeButton = removeButton(self.ak3path)
        self.editButton = editButton()
        self.type = 'timeVarDat'

        self.amp = QLineEdit('1.')
        self.dirX = QLineEdit('1.')
        self.dirY = QLineEdit('1.')
        self.dirZ = QLineEdit('1.')
        self.c = QLineEdit('340.')
        self.ffttime = QLineEdit('1.')

        self.loadButton = ak3LoadButton(self.ak3path)
        self.loadButton.clicked.connect(self.getFilename)

        self.label = QLabel('Distr. Time Domain')
        self.ampLabel = QLabel(self.amp.text() + ' Pa')
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.ampLabel, self.drawCheck, self.editButton]]
        #
        self.initSetupWindow()
        self.findRelevantPoints()
        self.sp = self.surfacePoints

        self.init3DActor(vtkWindow)

        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        #
        self.editButton.clicked.connect(self.showEdit)

        var = self.showEdit()
        if var == 0: # is the case if the initial setup window is canceled by the user
            #self.generatePressure()
            self.update3DActor()

        self.nearestNeighbor()
        self.timeToFreq()
        self.matchDataPoints()
        self.getPhases()


    # Clear all content in planeWave layout
    def clearLayout(self):
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))

    # Return x, y data for plotting; for plane wave: constant amplitude
    def getXYdata(self):
        return self.myModel.calculationObjects[0].frequencies, len(self.myModel.calculationObjects[0].frequencies)*[float(self.amp.text())]
        #return self.xf, len(self.xf)*[float(self.amp.text())]




    ##loads file. must be .json and must be a dict like: {'[x0,y0,z0]': [1,2,3,4,5...], ...'}
    def loadData(self, filename):
        #self.getFilename()
        with open(filename) as f:
            ld = json.load(f)
        keys = list(ld.keys())
        values = ld.values()
        for npt, pt in enumerate(keys):
            ptlist = pt[1:-1].split(',')
            keys[npt] = [float(x.strip()) for x in ptlist]
        keystup = [tuple(point) for point in keys]
        self.ld = dict(zip(keystup, values))
        self.ldkeys = keys
        self.timeValues = list(values)

    #    print(self.timeValues[0])
        ## aus Tupeln dringend Listen machen. Die als String in der dict speichern.
        ## Problem ist nämlich: Werte in Tupeln werden ungeordnet gespeichert. Das wirft evtl. die Koordinaten durcheinander.
        ## Die werden ja eh ständig in Listen und strings konvertiert.


    # finds next elements to given data points, writes into a proximity list, which can then be applied to the elements list
    def nearestNeighbor(self):
        self.findRelevantPoints()
        self.sp = self.surfacePoints
        #print(self.sp)
        surfdata = np.array(self.sp)
        #xyzdata = np.array([list(x) for x in list(self.ld.keys())])
        xyzdata = np.array(self.ldkeys)
        #np.random.shuffle(xyzdata)
        dist = np.empty(shape=(len(xyzdata), len(surfdata), 3))
        for k in range(len(xyzdata)):
            for i in range(len(surfdata)):
                diff = (xyzdata[k] - surfdata[i])
                dist[k,i,0] = diff[0]
                dist[k,i,1] = diff[1]
                dist[k,i,2] = diff[2]

        eucl = np.sqrt(np.square(dist[:,:,0]) + np.square(dist[:,:,1]) + np.square(dist[:,:,2]))
        self.euclNearest = []
        for p in range(len(eucl)):
            self.euclNearest.append(eucl[p].argsort()[0])
        #print(self.euclNearest, len(self.euclNearest))
        #print('xyz: ', len(self.ldkeys), 'surf: ', len(self.sp))

    ## combines nearest points and data: writes into a list of length of the element list
    def matchDataPoints(self):
        self.FreqData = [0 for x in self.sp]#np.zeros(shape=(len(self.sp)))
        i=0
        for x in self.euclNearest:
            self.FreqData[x] = self.FreqValues[i]
            i+=1
        #print(self.euclNearest, self.FreqData[0][123])
        #surfaceTimeData = dict(zip([(str(list(self.sp[x]))) for x in self.euclNearest], self.ld.values()))
        #print(surfaceTimeData.keys(), len(surfaceTimeData.keys()))


    # uses time data out of the laoded file to calculate a fft.
    def timeToFreq(self):
        self.FreqValues = []
        self.freqLenVec = []
        for nd, data in enumerate(self.timeValues):
            N=len(data)
            T=1/N
            Y = np.fft.fft(np.array(data))
            yf = 2.0/N * (Y[:N//2])
            self.FreqValues.append(yf.tolist())
            self.xf = np.linspace(0.0, 1.0/(2.0*T), N/2)
            self.freqLenVec.append(len(self.xf))
            self.myModel.calculationObjects[0].frequencies = np.linspace(0.0, 1.0/(2.0*T), N/2)
        #print(self.xf)
        #print(self.freqLenVec)
            #fig, ax = plt.subplots()
            #ax.plot(xf, 2.0/N * np.abs(yf[:N//2]))
            #plt.show()

    # calculates phases out of complex frequency domain data
    def getPhases(self):
        self.surfacePhases = np.zeros((max(self.freqLenVec),len(self.sp)))
        for nf in range(max(self.freqLenVec)):
            for ne in range(len(self.sp)):
                if self.FreqData[ne] == 0:
                    self.surfacePhases[nf,ne] = 0
                else:
                    self.surfacePhases[nf,ne] = cmath.phase(self.FreqData[ne][nf])
        #print(self.surfacePhases)

    # initialize vtk objects
    def init3DActor(self, vtkWindow):
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
        self.setupWindow = setupWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Amplitude'), self.amp)
        self.setupWindow.layout.addRow(QLabel('Speed of Sound'), self.c)
        self.setupWindow.layout.addRow(QLabel('Time difference between samples'), self.ffttime)
        self.setupWindow.layout.addWidget(self.loadButton)


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
            #try:
            #if float(self.radius.text()) == 0. and float(self.samples.text()) == 0.:
                #raise Exception
            self.ampLabel.setText(str(float(self.amp.text())) + ' Pa')
            #self.radLabel.setText('Radius: ' + self.radius.text())
            #self.sampLabel.setText('Sources: ' + self.samples.text())
            c = float(self.c.text()) # It's just a check, variable is not used here
            #self.generatePressure()
            #self.generatePointCloud()
            self.update3DActor()
            self.switch()
            #except: # if input is wrong, show message and reset values
                # messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                # self.resetValues()
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

        # Update load
        arrowPointLoad = vtk.vtkPoints()
        [arrowPointLoad.InsertNextPoint([point[0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], point[1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], point[2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p, point in enumerate(self.surfacePoints)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.1*scaleFactor*vec[0], -0.1*scaleFactor*vec[1], -0.1*scaleFactor*vec[2]]) for vec in self.surfaceElementNormals]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()

    #Open menu to choose file which contains point/time data
    def getFilename(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(None,"QFileDialog.getOpenFileName()", "","All Files (*);;json Files (*.json)", options=options)
        if fileName:
            self.filename = fileName
        datanew = self.loadData(fileName) #calls loadData function to read the file

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
            print(self.surfacePhases)
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













##
