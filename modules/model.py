###########################################################
### Common standard classes for entire python framework ###
###########################################################

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QApplication, QPushButton
from PyQt5.QtCore import Qt
import vtk
from vtk.util import numpy_support
import numpy as np
import copy
from lxml import etree
import h5py
from standardWidgets import progressWindow, editButton, editWindowBasic

# Saves a model, objects created by readModels()
class model: # Saves a model
    def __init__(self):
        self.name = ' - '
        self.initModelInfo()
        self.initLayout()
        self.reset()
    
    def reset(self): 
        self.fileEnding = ''
        self.name = ' - '
        self.path = ''
        self.hdf5File = 0
        self.cluster = 0
        self.nodes = 0
        self.nodeSets = []
        self.elems = []
        self.elementSets = []
        self.loads = []
        self.materials = []
        self.freqStart = np.float64(10.)
        self.freqSteps = np.uint64(10)
        self.freqDelta = np.float64(10.)
        self.frequencies = np.array([self.freqStart+n*self.freqDelta for n in range(self.freqSteps)]) # freqs are saved here readFreqs()
        self.analysisType = 'frequency' # stores the analysis type used to determine proper postprocessing and visualising
        self.solverType = 'elpasoC'
        self.analysisID = np.uint64(0)
        self.revision = np.uint64(6)
        self.description = 'my problem'
        self.nodeInfo.setText('Nodes: - ')
        self.elementInfo.setText('Blocks: - ')
        self.frequencyInfo.setText('Frequencies: - \n ')
        self.blockInfo.setRowCount(len(self.elems))
    
    #def saveAndExit(self):
        #
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
        #
        # for load in self.loads:
            # load.writeXML(self.binfilename, self.name, self.cluster)
        #
        # with h5py.File(self.binfilename, 'r+') as binfile:
            # if binfile.get('/Materials') is not None:
                # binfile.__delitem__('/Materials')
            # matList = binfile.create_group('Materials')
            # for i, mat in enumerate(self.calculationObjects[-1].materials):
                # type = mat[0]
                # name = mat[1]

                # mat = [float(x) for x in mat[2:]]
                # set = binfile.create_dataset('/Materials/mat'+str(i), data=mat)
                # set.attrs['type'] = type
                # set.attrs['name'] = name
        #
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
        
    def updateModelSetup(self):
        self.nodeInfo.setText('Nodes: ' + str(self.nodes[:]['Ids'].shape[0]))
        self.elementInfo.setText('Blocks: ' + str(len(self.elems)))
        self.blockInfo.setRowCount(len(self.elems))
        self.frequencies = np.array([self.freqStart+n*self.freqDelta for n in range(self.freqSteps)])
        addInfo = '\n                      (df=' + str(self.frequencies[1]-self.frequencies[0]) + ' Hz)'
        #if self.calculationObjects[-1].frequencyFile == 1:
        #    addInfo = '\n                      (from frq file)'
        self.frequencyInfo.setText('Frequencies: ' + str(min(self.frequencies)) + ' - ' + str(max(self.frequencies)) + ' Hz' + addInfo)
        
    def updateModel(self, vtkWindow):
        # UPDATE WIDGETS
        self.title.setText('Name: ' + self.name)
        if self.name is not ' - ':
            # Update Infobox
            self.updateModelSetup()
            # VTK Points
            self.vtkPoints = vtk.vtkPoints()
            self.vtkPoints.SetData(numpy_support.numpy_to_vtk(np.array([self.nodes[:]['xCoords'], self.nodes[:]['yCoords'], self.nodes[:]['zCoords']]).T)) # Attention - vtk points simply count from 0
            # Loop over all blocks
            vtkWindow.grids = []
            vtkWindow.mappers = []
            vtkWindow.edgeMappers = []
            vtkWindow.actors = []
            vtkWindow.edgeActors = []
            #
            progWin = progressWindow(len(self.elems)-1, 'Updating window')
            #
            for m, block in enumerate(self.elems):
                # VTK Elements
                newGrid = vtk.vtkUnstructuredGrid()
                newGrid.SetPoints(self.vtkPoints)
                # Loop over all elements in block m; elem is a list with elements ids and connected nodes
                for elemCount in range(block.shape[0]):
                    quad_ = vtk.vtkQuad()
                    [quad_.GetPointIds().SetId(p, int(np.where(self.nodes[:]['Ids'] == block[elemCount,p+1])[0])) for p in range(4)] # Get correct 4 node positions and insert node (nodes can have any id in elpaso)
                    newGrid.InsertNextCell(quad_.GetCellType(), quad_.GetPointIds())
                # Infotable
                items = [QTableWidgetItem(), QTableWidgetItem(block.attrs['ElementType'][:]), QTableWidgetItem(str(block.attrs['Id'][()])), QTableWidgetItem(str(block.shape[0]))]
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

