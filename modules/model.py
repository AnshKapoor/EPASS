###########################################################
### Common standard classes for entire python framework ###
###########################################################

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QApplication, QPushButton
from PyQt5.QtCore import Qt
import vtk
import numpy as np
import copy
from lxml import etree
import h5py
from standardWidgets import progressWindow, editButton, editWindowBasic

# Saves a model, objects created by readModels()
class model: # Saves a model
    def __init__(self):
        self.name = ' - '
        self.path = ''
        self.cluster = 0
        self.loads = []
        self.initModelInfo()
        self.initLayout()
        self.initLayout()
        self.calculationObjects = [] # For each model several calculations are possible (e.g. parameter variations)

    def exportOld(self):
        exportAK3 = copy.deepcopy(self.ak3tree)
        elemLoads = exportAK3.find('ElemLoads')
        elemLoads.set('N', '0')
        loadedElems = exportAK3.find('LoadedElems')
        # Delete old elem load entries
        for elemLoad in elemLoads.findall('ElemLoad'):
            elemLoads.remove(elemLoad)
        for loadedElem in loadedElems.findall('LoadedElem'):
            loadedElems.remove(loadedElem)
        # Create new entries for requested loads
        for load in self.loads:
            load.writeXML(exportAK3, self.binfilename, self.name, self.cluster)
        self.writeToFile(self.binfilename,[self.calculationObjects[0].nodes])
        # Write new ak3 file to disc
        progWin = progressWindow(2, 'Writing input file')
        with open(self.path + '/' + self.name + '_old.ak3', 'wb') as f:
            f.write(etree.tostring(self.ak3tree))
        progWin.setValue(1)
        QApplication.processEvents()
        with open(self.path + '/' + self.name + '.ak3', 'wb') as f:
            f.write(etree.tostring(exportAK3))
        progWin.setValue(2)
        QApplication.processEvents()

    def export(self):
        #exportAK3 = copy.deepcopy(self.ak3tree)
        #elemLoads = exportAK3.find('ElemLoads')
        #elemLoads.set('N', '0')
        #loadedElems = exportAK3.find('LoadedElems')
        # Delete old elem load entries
        # for elemLoad in elemLoads.findall('ElemLoad'):
        #     elemLoads.remove(elemLoad)
        # for loadedElem in loadedElems.findall('LoadedElem'):
        #     loadedElems.remove(loadedElem)
        # Create new entries for requested loads
        for load in self.loads:
            load.writeXML(self.binfilename, self.name, self.cluster)

        with h5py.File(self.binfilename, 'r+') as binfile:
            if binfile.get('/Materials') is not None:
                binfile.__delitem__('/Materials')
            matList = binfile.create_group('Materials')
            for i, mat in enumerate(self.calculationObjects[-1].materials):
                type = mat[0]
                name = mat[1]

                mat = [float(x) for x in mat[2:]]
                set = binfile.create_dataset('/Materials/mat'+str(i), data=mat)
                set.attrs['type'] = type
                set.attrs['name'] = material


        print('exported')
        #self.writeToFile(self.binfilename,[self.calculationObjects[0].nodes])
        #self.writeToFile(self.binfilename,[self.calculationObjects[0].nodes])
        # Write new ak3 file to disc
        #progWin = progressWindow(2, 'Writing input file')
        # with open(self.path + '/' + self.name + '_old.ak3', 'wb') as f:
        #     f.write(etree.tostring(self.ak3tree))
        # progWin.setValue(1)
        # QApplication.processEvents()
        # with open(self.path + '/' + self.name + '.ak3', 'wb') as f:
        #     f.write(etree.tostring(exportAK3))
        # progWin.setValue(2)
        QApplication.processEvents()


    def initModelInfo(self):
        # CREATE WIDGETS
        self.title = QLabel('Name: ' + self.name)
        self.title.setFixedWidth(200)
        self.nodeInfo = QLabel('Nodes: - ')
        self.elementInfo = QLabel('Blocks: - ')
        self.frequencyInfo = QLabel('Frequencies: - \n ')

        self.blockInfo = QTableWidget(1,4)
        self.blockInfo.verticalHeader().setVisible(False)
        self.blockInfo.setHorizontalHeaderLabels(['', 'Block ID', 'Element type', '#Elements'])
        [self.blockInfo.setColumnWidth(X, 100) for X in range(4)]
        self.blockInfo.setColumnWidth(0, 20)
        self.blockInfo.setFixedWidth(322)
        self.blockInfo.setFixedHeight(200)

    def initLayout(self):
        # ADD TO LAYOUT
        self.sublayout1 = QVBoxLayout()
        self.sublayout1.addWidget(self.title)
        self.sublayout1.addWidget(self.nodeInfo)
        self.sublayout1.addWidget(self.elementInfo)
        self.sublayout1.addWidget(self.frequencyInfo)
        self.sublayout1.addStretch(1)
        self.layout = QHBoxLayout()
        self.layout.addLayout(self.sublayout1)
        self.layout.addWidget(self.blockInfo)

    def updateModelInfo(self, vtkWindow):
        # UPDATE WIDGETS
        self.title.setText('Name: ' + self.name)
        if len(self.calculationObjects) > 0:
            # VTK Points
            self.vtkPoints = vtk.vtkPoints()
            [self.vtkPoints.InsertNextPoint(float(node[1]), float(node[2]), float(node[3])) for node in self.calculationObjects[0].nodes]
            # Infobox
            self.nodeInfo.setText('Nodes: ' + str(len(self.calculationObjects[0].nodes)))
            self.elementInfo.setText('Blocks: ' + str(len(self.calculationObjects[0].elems)))
            addInfo = '\n                      (df=' + str(self.calculationObjects[-1].frequencies[1]-self.calculationObjects[-1].frequencies[0]) + ' Hz)'
            if self.calculationObjects[-1].frequencyFile == 1:
                addInfo = '\n                      (from frq file)'
            self.frequencyInfo.setText('Frequencies: ' + str(min(self.calculationObjects[-1].frequencies)) + ' - ' + str(max(self.calculationObjects[-1].frequencies)) + ' Hz' + addInfo)
            self.blockInfo.setRowCount(len(self.calculationObjects[0].elems))
            # Loop over all blocks
            vtkWindow.grids = []
            vtkWindow.mappers = []
            vtkWindow.edgeMappers = []
            vtkWindow.actors = []
            vtkWindow.edgeActors = []
            progWin = progressWindow(len(self.calculationObjects[0].elems)-1, 'Updating window')
            for m, block in enumerate(self.calculationObjects[0].elems):
                # VTK Elements
                newGrid = vtk.vtkUnstructuredGrid()
                newGrid.SetPoints(self.vtkPoints)
                # Loop over all elements in block m; elem is a list with elements ids and connected nodes
                for elem in block[2]:
                    quad_ = vtk.vtkQuad()
                    for p in range(4): # Set four nodes
                        correctNodePosition = int(np.where(self.calculationObjects[0].nodes[:,0] == elem[p+1])[0]) # Get correct node position (nodes can have any id in elpaso)
                        quad_.GetPointIds().SetId(p, int(correctNodePosition))
                    newGrid.InsertNextCell(quad_.GetCellType(), quad_.GetPointIds())
                # Infotable
                items = [QTableWidgetItem(), QTableWidgetItem(str(block[1])), QTableWidgetItem(str(block[0])), QTableWidgetItem(str(len(block[2])))]
                for n, item in enumerate(items):
                    if n==0: # Checkbox
                        item.setFlags( Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                        item.setCheckState(Qt.Checked)
                    else: # Text/Info
                        item.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                    item.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
                    self.blockInfo.setItem(m, n, item)
                vtkWindow.grids.append(newGrid)
                # Each block gets a vtk actor and mapper
                vtkWindow.mappers.append(vtk.vtkDataSetMapper())
                vtkWindow.mappers[-1].SetInputData(vtkWindow.grids[-1])
                vtkWindow.actors.append(vtk.vtkActor())
                vtkWindow.actors[-1].SetMapper(vtkWindow.mappers[-1])
                vtkWindow.actors[-1].GetProperty().SetAmbient(0.9)
                vtkWindow.actors[-1].GetProperty().SetDiffuse(0.1)
                vtkWindow.actors[-1].GetProperty().SetSpecular(0.)
                # Each block gets another vtk actor and mapper for the edges of the grid
                vtkWindow.edgeMappers.append(vtk.vtkDataSetMapper())
                vtkWindow.edgeMappers[-1].SetInputData(vtkWindow.grids[-1])
                vtkWindow.edgeActors.append(vtk.vtkActor())
                vtkWindow.edgeActors[-1].SetMapper(vtkWindow.edgeMappers[-1])
                vtkWindow.edgeActors[-1].GetProperty().SetRepresentationToWireframe()
                vtkWindow.edgeActors[-1].GetProperty().SetLineWidth(2)
                vtkWindow.edgeActors[-1].GetProperty().SetColor(0.1,0.1,0.1)
                progWin.setValue(m+1)
                QApplication.processEvents()

    def toggleCluster(self):
        if self.cluster == 0:
            self.cluster = 1
        else:
            self.cluster = 0


    def writeToFile(self,binFile,objList):
        with h5py.File(binFile, 'r+') as fileObj:
            name='mtxFemNodes'
            for no, obj in enumerate(objList):
                # if obj == self.calculationObjects[0].nodes:
                #     name = 'nodes'
                if fileObj.get('/Nodes') is not None:
                    fileObj.__delitem__('/Nodes')
                set = fileObj.create_dataset('/Nodes/'+name, data = obj)
                set.attrs['MethodType'] = 'FEM'


# Saves one calculation
class calculationObject: # Saves one calculation in frequency domain
    def __init__(self, name):
        #add nodes to the table again!
        self.LookUpTable = ['elements']#,'nodes'] #contains a string for each element, that will be stored somewhere. !yet to be filled!
        self.name = name
        self.filename = name
        self.frequencyObjects = [] # Each calculation_object consists of several frequency_objects (one frequency step)
        self.nodes = [] # Nodes are saved here by readNodes()
        self.elems = [] # elements are saved here by readElems()
        self.materials = []
        self.nodesets = []
        self.freqSteps = 1
        self.freqDelta = 1
        self.freqStart = 1
        self.frequencies = [] # freqs are saved here readFreqs()
        self.frequencyFile = 0
        self.stepValues = [] # should replace self.frequencies list considering time and frequency domain support
        self.physicalValues = [] # stores information on supported physical values
        self.analysisType = 'undefined' # stores the analysis type used to determine proper postprocessing and visualising
        self.solver = 'undefined'
        self.doPreCalculationRayleigh = 0
