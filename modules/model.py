###########################################################
### Common standard classes for entire python framework ###
###########################################################

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QApplication, QComboBox, QCheckBox, QFileDialog
from PyQt5.QtCore import Qt
import vtk
from vtk.util import numpy_support
import numpy as np
from standardWidgets import progressWindow, addButton, addInterfaceWindow, messageboxOK
from standardFunctionsGeneral import getVTKElem, identifyAlternativeElemTypes, searchInterfaceElems, getPossibleInterfacePartner, identifyOrientationTypes, isPlateType

# Saves a model, objects created by readModels()
class model(QWidget): # Saves a model
    def __init__(self):
        super(model, self).__init__()
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
        self.elemsInv = []
        self.elemsInvTags = []
        self.interfaceElems = []
        self.elementSets = []
        self.loads = []
        self.materials = []
        self.constraints = []
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
        self.blockMaterialSelectors = []
        self.blockElementTypeSelectors = []
        self.blockOrientationSelectors = []
    
    def initModelInfo(self):
        # CREATE WIDGETS
        self.title = QLabel('Name: ' + self.name)
        self.title.setFixedWidth(150)
        self.nodeInfo = QLabel('Nodes: - ')
        self.elementInfo = QLabel('Blocks: - ')
        self.frequencyInfo = QLabel('Frequencies: - \n ')

        self.blockInfo = QTableWidget(1,6)
        self.blockInfo.verticalHeader().setVisible(False)
        self.blockInfo.setHorizontalHeaderLabels(['', 'ID', '#Elems', 'Element type', 'Material', 'Orient.'])
        [self.blockInfo.setColumnWidth(n, width) for n, width in enumerate([50,50,65,85,70,55])]
        self.blockInfo.setColumnWidth(0, 20)
        self.blockInfo.setFixedWidth(347)
        self.blockInfo.setFixedHeight(250)
        
        self.interFaceElemAddButton = addButton()
        
        self.blockMaterialSelectors = []
        self.blockElementTypeSelectors = []
        self.blockOrientationSelectors = []

    def initLayout(self):
        # ADD TO LAYOUT
        self.sublayout1 = QVBoxLayout()
        self.sublayout1.addWidget(self.title)
        self.sublayout1.addWidget(self.nodeInfo)
        self.sublayout1.addWidget(self.elementInfo)
        self.sublayout1.addWidget(self.frequencyInfo)
        self.sublayout1.addStretch(1)
        self.sublayout2 = QVBoxLayout()
        self.sublayout2.addWidget(self.blockInfo)
        self.sublayout3 = QHBoxLayout()
        [self.sublayout3.addWidget(wid) for wid in [QLabel('Add interface elements'), self.interFaceElemAddButton]]
        self.sublayout3.addStretch(1)
        self.sublayout2.addLayout(self.sublayout3)
        self.sublayout2.addStretch(1)
        self.layout = QHBoxLayout()
        self.layout.addLayout(self.sublayout1)
        self.layout.addLayout(self.sublayout2)
    
    def updateOrientationSelector(self):
        idx = self.blockElementTypeSelectors.index(self.sender())
        [self.blockOrientationSelectors[idx].removeItem(n) for n in range(self.blockOrientationSelectors[idx].count()-1,-1,-1)]
        [self.blockOrientationSelectors[idx].addItem(orientType) for orientType in identifyOrientationTypes(self.sender().currentText())]
        
    def updateBlockMaterialSelector(self):
        for n in range(len(self.blockMaterialSelectors)):
            oldSelection = self.blockMaterialSelectors[n].currentText()
            [self.blockMaterialSelectors[n].removeItem(p) for p in range(self.blockMaterialSelectors[n].count()-1,-1,-1)]
            [self.blockMaterialSelectors[n].addItem(mat.Id.text()) for mat in self.materials]
            allNewItems = [self.blockMaterialSelectors[n].itemText(p) for p in range(self.blockMaterialSelectors[n].count())]
            if oldSelection in allNewItems: 
                self.blockMaterialSelectors[n].setCurrentIndex(allNewItems.index(oldSelection))
    
    def autoAssignBlockMaterialSelectors(self):
        for n in range(len(self.blockMaterialSelectors)):
            if self.blockMaterialSelectors[n].count() >= n+1:
                self.blockMaterialSelectors[n].setCurrentIndex(n)
        
    def updateModelSetup(self, inputProblem=False):
        self.nodeInfo.setText('Nodes: ' + str(self.nodes[:]['Ids'].shape[0]))
        self.elementInfo.setText('Blocks: ' + str(len(self.elems)))
        self.blockInfo.setRowCount(len(self.elems))
        if inputProblem:
            self.frequencyInfo.setText('Frequencies: Wrong input')
        else:
            self.frequencies = np.array([self.freqStart+n*self.freqDelta for n in range(self.freqSteps)])
            addInfo = '\n                      (df=' + str(self.frequencies[1]-self.frequencies[0]) + ' Hz)'
            #if self.calculationObjects[-1].frequencyFile == 1:
            #    addInfo = '\n                      (from frq file)'
            self.frequencyInfo.setText('Frequencies: ' + str(min(self.frequencies)) + ' - ' + str(max(self.frequencies)) + ' Hz' + addInfo)
        
    def updateModel(self, vtkWindow):
        # UPDATE WIDGETS
        self.title.setText('Name: ' + self.name)
        if self.name != ' - ':
            # Update Infobox
            self.updateModelSetup()
            self.interfaceDialogWindow = addInterfaceWindow()
            self.interfaceblockChecker = []
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
                # Material and element selector
                self.blockElementTypeSelectors.append(QComboBox())
                self.blockElementTypeSelectors[-1].setStyleSheet("background-color:rgb(255,255,255)")
                [self.blockElementTypeSelectors[-1].addItem(elementType) for elementType in identifyAlternativeElemTypes(block.attrs['ElementType'])]
                self.blockElementTypeSelectors[-1].currentIndexChanged.connect(self.updateOrientationSelector)
                self.blockMaterialSelectors.append(QComboBox())
                self.blockMaterialSelectors[-1].setStyleSheet("background-color:rgb(255,255,255)")
                self.blockOrientationSelectors.append(QComboBox())
                self.blockOrientationSelectors[-1].setStyleSheet("background-color:rgb(255,255,255)")
                [self.blockOrientationSelectors[-1].addItem(orientType) for orientType in identifyOrientationTypes(block.attrs['ElementType'])]
                # Block selection for interface dialog
                self.interfaceblockChecker.append(QCheckBox())
                subLayout = QHBoxLayout()
                [subLayout.addWidget(wid) for wid in [self.interfaceblockChecker[-1], QLabel('Block ' + str(block.attrs['Id']))]]
                subLayout.addStretch()
                self.interfaceDialogWindow.blockLayout.addLayout(subLayout)
                # VTK Elements
                newGrid = vtk.vtkUnstructuredGrid()
                newGrid.SetPoints(self.vtkPoints)
                #
                vtkCells = vtk.vtkCellArray()
                newElem, newElemTypeId, nnodes = getVTKElem(block.attrs['ElementType'])
                cells = np.zeros((block.shape[0],nnodes+1), dtype=np.int64)
                cells[:,0] = nnodes
                for elemCount in range(block.shape[0]):
                    cells[elemCount,1:] = [self.nodesInv[ID] for ID in block[elemCount,1:(nnodes+1)]]
                vtkCells.SetCells(block.shape[0], numpy_support.numpy_to_vtk(cells, deep = 1, array_type = vtk.vtkIdTypeArray().GetDataType()))
                newGrid.SetCells(newElemTypeId, vtkCells)
                # Infotable
                items = [QTableWidgetItem(), QTableWidgetItem(str(block.attrs['Id'][()])), QTableWidgetItem(str(block.shape[0]))]
                for n, item in enumerate(items):
                    if n==0: # Checkbox
                        item.setFlags( Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                        item.setCheckState(Qt.Checked)
                    else: # Text/Info
                        item.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                    item.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
                    self.blockInfo.setItem(m, n, item)
                self.blockInfo.setCellWidget(m, 3, self.blockElementTypeSelectors[-1])
                self.blockInfo.setCellWidget(m, 4, self.blockMaterialSelectors[-1])
                self.blockInfo.setCellWidget(m, 5, self.blockOrientationSelectors[-1])
                #
                vtkWindow.grids.append(newGrid)
                # Each block gets a vtk actor and mapper
                vtkWindow.mappers.append(vtk.vtkDataSetMapper())
                vtkWindow.mappers[-1].SetInputData(vtkWindow.grids[-1])
                vtkWindow.actors.append(vtk.vtkActor())
                vtkWindow.actors[-1].SetMapper(vtkWindow.mappers[-1])
                vtkWindow.actors[-1].GetProperty().SetAmbient(0.9)
                vtkWindow.actors[-1].GetProperty().SetDiffuse(0.1)
                vtkWindow.actors[-1].GetProperty().SetSpecular(0.)
                vtkWindow.actors[-1].GetProperty().SetOpacity(0.85)
                vtkWindow.actors[-1].GetProperty().SetColor(0.3,0.3,0.3)
                # Each block gets another vtk actor and mapper for the edges of the grid
                vtkWindow.edgeMappers.append(vtk.vtkDataSetMapper())
                vtkWindow.edgeMappers[-1].SetInputData(vtkWindow.grids[-1])
                vtkWindow.edgeActors.append(vtk.vtkActor())
                vtkWindow.edgeActors[-1].SetMapper(vtkWindow.edgeMappers[-1])
                vtkWindow.edgeActors[-1].GetProperty().SetRepresentationToWireframe()
                vtkWindow.edgeActors[-1].GetProperty().SetLineWidth(3)
                vtkWindow.edgeActors[-1].GetProperty().SetColor(0.7,0.7,0.7)
                progWin.setValue(m+1)
                QApplication.processEvents()

    def toggleCluster(self):
        if self.cluster == 0:
            self.cluster = 1
        else:
            self.cluster = 0
    
    def interfaceElemDialog(self, vtkWindow):
        var = self.interfaceDialogWindow.exec_()
        if var == 0: # cancel
            pass
        elif var == 1: # interface requested
            relevantBlockCombinations = []
            for m, checkButton1 in enumerate(self.interfaceblockChecker):
                if checkButton1.isChecked(): # Block selected?
                    for n, checkButton2 in enumerate(self.interfaceblockChecker):
                        if checkButton2.isChecked():  # Block selected?
                            if m!=n:
                                elemType1 = self.blockElementTypeSelectors[m].currentText()
                                elemType2 = self.blockElementTypeSelectors[n].currentText()
                                if elemType1 in getPossibleInterfacePartner(elemType2): # Compatible element types?
                                    if isPlateType(elemType1):
                                        relevantBlockCombinations.append([n,m]) 
                                    else:
                                        relevantBlockCombinations.append([m,n])
            if relevantBlockCombinations:
                foundInterFaceElements = searchInterfaceElems(self.nodes, self.nodesInv, self.elems, np.unique(np.array(relevantBlockCombinations), axis=0))
                if foundInterFaceElements: 
                    # Add information to info block
                    noOfInterfaceElems = len(foundInterFaceElements)
                    self.blockInfo.insertRow(self.blockInfo.rowCount())
                    currentRow = self.blockInfo.rowCount()-1
                    items = [QTableWidgetItem(), QTableWidgetItem(' '), QTableWidgetItem('interface'), QTableWidgetItem(' '), QTableWidgetItem(' ')]
                    for n, item in enumerate(items):
                        if n==0: # Checkbox
                            item.setFlags( Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                            item.setCheckState(Qt.Checked)
                        else: # Text/Info
                            item.setFlags( Qt.ItemIsSelectable |  Qt.ItemIsEnabled )
                        item.setTextAlignment( Qt.AlignHCenter | Qt.AlignVCenter )
                        self.blockInfo.setItem(currentRow, n, item)
                    # Create actors for 3D window
                    # VTK Elements
                    newGrid = vtk.vtkUnstructuredGrid()
                    newGrid.SetPoints(self.vtkPoints)
                    #
                    vtkCells = vtk.vtkCellArray()
                    newElem, newElemTypeId, nnodes = getVTKElem(self.elems[foundInterFaceElements[-1].structBlockIdx].attrs['ElementType'])
                    cells = np.zeros((noOfInterfaceElems,nnodes+1), dtype=np.int64)
                    cells[:,0] = nnodes
                    for elemCount in range(noOfInterfaceElems):
                        cells[elemCount,1:] = [self.nodesInv[nodeID] for nodeID in foundInterFaceElements[elemCount].structuralNodes[:4]]
                    vtkCells.SetCells(noOfInterfaceElems, numpy_support.numpy_to_vtk(cells, deep = 1, array_type = vtk.vtkIdTypeArray().GetDataType()))
                    newGrid.SetCells(newElemTypeId, vtkCells)
                    #
                    vtkWindow.grids.append(newGrid)
                    # Each block gets a vtk actor and mapper
                    vtkWindow.mappers.append(vtk.vtkDataSetMapper())
                    vtkWindow.mappers[-1].SetInputData(vtkWindow.grids[-1])
                    vtkWindow.actors.append(vtk.vtkActor())
                    vtkWindow.actors[-1].SetMapper(vtkWindow.mappers[-1])
                    vtkWindow.actors[-1].GetProperty().SetColor(0.1,0.1,0.7)
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
                    #
                    self.interfaceElems.append(foundInterFaceElements)
                    messageboxOK('Success', str(noOfInterfaceElems) + ' interface elements found. \n Select appropriate materials before export!')
                else:
                    messageboxOK('Error', 'No interfaces found.')
            else:
                messageboxOK('Error', 'Select more than one block and select compatible block.')
        
    def data2hdf5(self): 
        try:
            # Sort blocks according to ID
            groupIDs = []
            allBlocks = []
            for block in self.hdf5File['Elements'].keys():
                groupIDs.append(self.hdf5File['Elements/' + block].attrs['Id'])
                allBlocks.append(block)
            idx = np.argsort(np.array(groupIDs))
            allBlocks = [allBlocks[n] for n in idx]
            # Update blocks and receive maximum ID in correct order
            maxElemId = 0
            for n, block in enumerate(allBlocks):
                currentMaxId = self.hdf5File['Elements/' + block][:,0].max()
                if currentMaxId > maxElemId:
                    maxElemId = currentMaxId
                if self.blockMaterialSelectors[n].currentText() != '':
                    self.hdf5File['Elements/' + block].attrs['MaterialId'] = np.int64(self.blockMaterialSelectors[n].currentText())
                if self.blockElementTypeSelectors[n].currentText() != '':
                    self.hdf5File['Elements/' + block].attrs['ElementType'] = self.blockElementTypeSelectors[n].currentText()
                self.hdf5File['Elements/' + block].attrs['Orientation'] = self.blockOrientationSelectors[n].currentText()
                if self.blockOrientationSelectors[n].currentText() == 'user-def':
                    messageboxOK('File required', 'A user-defined material orientation for block ' + str(self.hdf5File['Elements/' + block].attrs['Id']) + ' selected. <br>Please select an ascii file containing the orientation.')
                    options = QFileDialog.Options()
                    options |= QFileDialog.DontUseNativeDialog
                    fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","ascii file (*.dat)", options=options)
                    if fileName:
                        myData = []
                        f = open(fileName, 'r')
                        for line in f:
                            myData.append([float(x) for x in line.split()])
                            self.hdf5File['Elements/' + block].attrs['OrientationFile'] = '/Parameters/orient' + str(self.hdf5File['Elements/' + block].attrs['Id'])
                        self.hdf5File['Parameters'].create_dataset('orient' + str(self.hdf5File['Elements/' + block].attrs['Id']), data=np.array(myData, dtype=np.float64))
                    else:
                        return 0
            # Export interfaces
            if not 'InterfaceElements' in self.hdf5File.keys():
                self.hdf5File.create_group('InterfaceElements')
            interfaceGroup = self.hdf5File['InterfaceElements']
            #
            for dataSet in interfaceGroup.keys():
                del interfaceGroup[dataSet]
            #
            counter = 0
            for interfaceBlock in self.interfaceElems:
                for interFaceElem in interfaceBlock:
                    interFaceElem.Id = np.uint64(maxElemId+1)
                    maxElemId = maxElemId+1
                    dataSet = interfaceGroup.create_dataset('InterfaceElement' + str(interFaceElem.Id), data=[])
                    dataSet.attrs['Id'] = np.uint64(interFaceElem.Id)
                    #
                    structMatId = np.uint64(self.blockMaterialSelectors[interFaceElem.structBlockIdx].currentText())
                    structMatIdx = self.blockMaterialSelectors[interFaceElem.structBlockIdx].currentIndex()
                    dataSet.attrs['matS'] = structMatId
                    #
                    fluidMatId = np.uint64(self.blockMaterialSelectors[interFaceElem.fluidBlockIdx].currentText())
                    fluidMatIdx = self.blockMaterialSelectors[interFaceElem.fluidBlockIdx].currentIndex()
                    dataSet.attrs['matF'] = fluidMatId
                    #
                    dataSet.attrs['ori'] = interFaceElem.ori
                    #
                    if self.materials[structMatIdx].type[:7] == 'STR_LIN': 
                        if self.materials[fluidMatIdx].type[:10] == 'AF_LIN_UAF': 
                            interFaceElem.type = 'InterfaceMindlin'
                            dataSet.attrs['type'] = 'InterfaceMindlin'
                        elif self.materials[fluidMatIdx].type[:10] in ['AF_LIN_DAF', 'AF_LIN_EQF']: 
                            interFaceElem.type = 'InterfaceMindlinEquiporo'
                            dataSet.attrs['type'] = 'InterfaceMindlinEquiporo'
                        else:
                            return 0
                    else:
                        return 0
                    # 
                    dataSet.attrs['NS'] = interFaceElem.structuralNodes
                    dataSet.attrs['NF'] = interFaceElem.fluidNodes
                    #
                    counter = counter + 1
            interfaceGroup.attrs['N'] = np.uint64(counter)
            return 1
        except:
            return 0
