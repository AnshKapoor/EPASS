###########################################################
### Common standard classes for entire python framework ###
###########################################################

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QApplication, QComboBox, QCheckBox, QFileDialog
from PyQt5.QtCore import Qt
import vtk
from vtk.util import numpy_support
import numpy as np
from standardWidgets import progressWindow, addButton, orthoCheckerButton, addInterfaceWindow, messageboxOK
from standardFunctionsGeneral import getVTKElem, identifyAlternativeElemTypes, searchInterfaceElems, searchNCInterfaceElemsSurface, getPossibleInterfacePartner, identifyOrientationTypes, isPlateType

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
        self.interNodesIds = []
        self.interNodesMaxId = 0
        self.interNodesCoords = []
        self.nodeSets = []
        self.elems = []
        self.elemsInv = []
        self.elemsInvTags = []
        self.interfaceElems = []
        self.NCinterfaceElems = []
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
        self.orthoCheckerButton = orthoCheckerButton()
        
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
        self.sublayout3.addWidget(self.orthoCheckerButton)
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
            #
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
                    print(elemCount)
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
                vtkWindow.edgeActors[-1].GetProperty().SetPointSize(7)
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
                if self.interfaceDialogWindow.methodSelector.currentText() == 'Matching nodes': 
                  foundInterFaceElementsBlocks = searchInterfaceElems(self.nodes, self.nodesInv, self.elems, np.unique(np.array(relevantBlockCombinations), axis=0))
                  foundNCInterFaceElementsBlocks = []
                elif self.interfaceDialogWindow.methodSelector.currentText() == 'Non-conform in plane': 
                  foundInterFaceElementsBlocks = []
                  foundNCInterFaceElementsBlocks = searchNCInterfaceElemsSurface(self.nodes, self.nodesInv, self.elems, np.unique(np.array(relevantBlockCombinations), axis=0), self.interNodesMaxId, 'plane')
                elif self.interfaceDialogWindow.methodSelector.currentText() == 'Non-conform in cylinder':
                  foundInterFaceElementsBlocks = []
                  foundNCInterFaceElementsBlocks = searchNCInterfaceElemsSurface(self.nodes, self.nodesInv, self.elems, np.unique(np.array(relevantBlockCombinations), axis=0), self.interNodesMaxId, 'cylinder')
                else:
                  foundInterFaceElementsBlocks = []
                  foundNCInterFaceElementsBlocks = []
                totalFoundInterfaces = 0
                for foundInterFaceElements in foundInterFaceElementsBlocks:
                    if foundInterFaceElements: 
                        # Add information to info block
                        noOfInterfaceElems = len(foundInterFaceElements)
                        self.blockInfo.insertRow(self.blockInfo.rowCount())
                        currentRow = self.blockInfo.rowCount()-1
                        items = [QTableWidgetItem(), QTableWidgetItem(' '), QTableWidgetItem(str(len(foundInterFaceElements))), QTableWidgetItem('inter (' + str(self.elems[foundInterFaceElements[0].structBlockIdx].attrs['Id']) + '/' + str(self.elems[foundInterFaceElements[0].fluidBlockIdx].attrs['Id']) + ')'), QTableWidgetItem(' ')]
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
                        totalFoundInterfaces = totalFoundInterfaces + noOfInterfaceElems
                for foundNCInterFaceElementsBlock in foundNCInterFaceElementsBlocks:
                    foundNCInterFaceElements = foundNCInterFaceElementsBlock[0]
                    if foundNCInterFaceElements: 
                        [self.interNodesIds.append(interNodeId) for interNodeId in foundNCInterFaceElementsBlock[1]]
                        self.interNodesMaxId = max(self.interNodesIds)
                        [self.interNodesCoords.append(interNodeCoords) for interNodeCoords in foundNCInterFaceElementsBlock[2]]
                        # Add information to info block
                        noOfNCInterfaceElems = len(foundNCInterFaceElements)
                        self.blockInfo.insertRow(self.blockInfo.rowCount())
                        currentRow = self.blockInfo.rowCount()-1
                        items = [QTableWidgetItem(), QTableWidgetItem(' '), QTableWidgetItem(str(len(foundNCInterFaceElements))), QTableWidgetItem('inter (' + str(self.elems[foundNCInterFaceElements[0].structBlockIdx].attrs['Id']) + '/' + str(self.elems[foundNCInterFaceElements[0].fluidBlockIdx].attrs['Id']) + ')'), QTableWidgetItem(' ')]
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
                        newElem, newElemTypeId, nnodes = getVTKElem(self.elems[foundNCInterFaceElements[-1].structBlockIdx].attrs['ElementType'])
                        cells = np.zeros((noOfNCInterfaceElems,nnodes+1), dtype=np.int64)
                        cells[:,0] = nnodes
                        for elemCount in range(noOfNCInterfaceElems):
                            cells[elemCount,1:] = [self.nodesInv[nodeID] for nodeID in foundNCInterFaceElements[elemCount].structuralNodes[:4]]
                        vtkCells.SetCells(noOfNCInterfaceElems, numpy_support.numpy_to_vtk(cells, deep = 1, array_type = vtk.vtkIdTypeArray().GetDataType()))
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
                        self.NCinterfaceElems.append(foundNCInterFaceElements)
                        totalFoundInterfaces = totalFoundInterfaces + noOfNCInterfaceElems
                if totalFoundInterfaces>0:
                    messageboxOK('Success', str(totalFoundInterfaces) + ' interface elements found in total. \n Select appropriate materials before export!')
                else:
                    messageboxOK('Error', 'No interfaces found.')
            else:
                messageboxOK('Error', 'Select more than one block and select compatible block.')
    
    def showShellOrientations(self, vtkWindow):
        # Prepare arrays for points and vector data
        self.centerOrientPoints = vtk.vtkPoints()
        self.xVectors = vtk.vtkDoubleArray()
        self.xVectors.SetNumberOfComponents(3)
        self.yVectors = vtk.vtkDoubleArray()
        self.yVectors.SetNumberOfComponents(3)
        # Loop over blocks
        for blockIdx in range(self.blockInfo.rowCount()):
            state = self.blockInfo.item(blockIdx,0).checkState()
            elemType = self.blockElementTypeSelectors[blockIdx].currentText()
            # Check for ticked checkbox and shell element type
            if state==2 and isPlateType(elemType):
                # Loop over elems and calc orientation (local x and y)
                progWin = progressWindow(len(self.elems[blockIdx])-1, 'Computing local orientations')
                progWin.setValue(0)
                QApplication.processEvents()
                for n, singleElem in enumerate(self.elems[blockIdx]):
                    nodeIdx = [self.nodesInv[nodeID] for nodeID in singleElem[1:]]
                    elemX = [self.nodes[idx]['xCoords'] for idx in nodeIdx]
                    elemY = [self.nodes[idx]['yCoords'] for idx in nodeIdx]
                    elemZ = [self.nodes[idx]['zCoords'] for idx in nodeIdx]                    
                    elemMean = [np.mean(elemX), np.mean(elemY), np.mean(elemZ)]
                    self.centerOrientPoints.InsertNextPoint(elemMean)   
                    # Plot orientation
                    localOrientX = [0.4*(elemX[1]+elemX[2])-0.4*(elemX[0]+elemX[3]), 0.4*(elemY[1]+elemY[2])-0.4*(elemY[0]+elemY[3]), 0.4*(elemZ[1]+elemZ[2])-0.4*(elemZ[0]+elemZ[3])]
                    localOrientY = [0.4*(elemX[2]+elemX[3])-0.4*(elemX[0]+elemX[1]), 0.4*(elemY[2]+elemY[3])-0.4*(elemY[0]+elemY[1]), 0.4*(elemZ[2]+elemZ[3])-0.4*(elemZ[0]+elemZ[1])]
                    self.xVectors.InsertNextTuple(localOrientX)
                    self.yVectors.InsertNextTuple(localOrientY)
                    progWin.setValue(n)
                    QApplication.processEvents()
        ### VTK data for X direction
        xData = vtk.vtkPolyData()
        xData.SetPoints(self.centerOrientPoints)
        xData.GetPointData().SetVectors(self.xVectors)
        arrowSource = vtk.vtkArrowSource()
        # Glyphs
        xGlyph = vtk.vtkGlyph3D()
        xGlyph.SetScaleModeToScaleByVector()
        xGlyph.SetSourceConnection(arrowSource.GetOutputPort())
        xGlyph.SetInputData(xData)
        xGlyph.Update()
        # Mapper
        xVectorMapper = vtk.vtkPolyDataMapper()
        xVectorMapper.SetInputConnection(xGlyph.GetOutputPort())
        # Actor
        self.xVectorActor = vtk.vtkActor()
        self.xVectorActor.GetProperty().SetColor(0.8, 0., 0.)
        self.xVectorActor.SetMapper(xVectorMapper)
        vtkWindow.ren.AddActor(self.xVectorActor)
        ### VTK data for Y direction
        yData = vtk.vtkPolyData()
        yData.SetPoints(self.centerOrientPoints)
        yData.GetPointData().SetVectors(self.yVectors)
        # Glyphs
        yGlyph = vtk.vtkGlyph3D()
        yGlyph.SetScaleModeToScaleByVector()
        yGlyph.SetSourceConnection(arrowSource.GetOutputPort())
        yGlyph.SetInputData(yData)
        yGlyph.Update()
        # Mapper
        yVectorMapper = vtk.vtkPolyDataMapper()
        yVectorMapper.SetInputConnection(yGlyph.GetOutputPort())
        # Actor
        self.yVectorActor = vtk.vtkActor()
        self.yVectorActor.GetProperty().SetColor(0., 0.8, 0.)
        self.yVectorActor.SetMapper(yVectorMapper)
        vtkWindow.ren.AddActor(self.yVectorActor)

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
            # Export interfaces; conform
            if not 'InterfaceElements' in self.hdf5File.keys():
                self.hdf5File.create_group('InterfaceElements')
            interfaceGroup = self.hdf5File['InterfaceElements']
            # non-conform
            if not 'NCInterfaceElements' in self.hdf5File.keys():
                self.hdf5File.create_group('NCInterfaceElements')
            NCinterfaceGroup = self.hdf5File['NCInterfaceElements']
            if not 'InterNodes' in self.hdf5File.keys():
                self.hdf5File.create_group('InterNodes')
            interNodesGroup = self.hdf5File['InterNodes']
            #
            for dataSet in interfaceGroup.keys():
                del interfaceGroup[dataSet]
            for dataSet in NCinterfaceGroup.keys():
                del NCinterfaceGroup[dataSet]
            # matching nodes
            counter = 0
            for blockID, interfaceBlock in enumerate(self.interfaceElems):
                #
                noOfStructNodes= len(interfaceBlock[0].structuralNodes)
                noOfFluidNodes = len(interfaceBlock[0].fluidNodes)
                #
                dataSet = interfaceGroup.create_dataset('InterfaceElements' + str(blockID), data=np.zeros((len(interfaceBlock), 2+noOfStructNodes+noOfFluidNodes), dtype=np.int64)) # Cols: Id, ori, structNodes, fluidNodes
                dataSet.attrs['NstructNodes'] = np.uint64(noOfStructNodes)
                dataSet.attrs['NfluidNodes'] = np.uint64(noOfFluidNodes)
                #
                structMatId = np.uint64(self.blockMaterialSelectors[interfaceBlock[0].structBlockIdx].currentText())
                structMatIdx = self.blockMaterialSelectors[interfaceBlock[0].structBlockIdx].currentIndex()
                dataSet.attrs['mats'] = structMatId
                #
                fluidMatId = np.uint64(self.blockMaterialSelectors[interfaceBlock[0].fluidBlockIdx].currentText())
                fluidMatIdx = self.blockMaterialSelectors[interfaceBlock[0].fluidBlockIdx].currentIndex()
                dataSet.attrs['matF'] = fluidMatId
                #
                if self.materials[structMatIdx].type[:7] == 'STR_LIN': 
                    if self.materials[fluidMatIdx].type[:10] == 'AF_LIN_UAF': 
                        dataSet.attrs['type'] = 'InterfaceMindlin'
                    elif self.materials[fluidMatIdx].type[:10] in ['AF_LIN_DAF', 'AF_LIN_EQF']: 
                        dataSet.attrs['type'] = 'InterfaceMindlinEquiporo'
                    else:
                        return 0
                else:
                    return 0
                #
                counter = counter + len(interfaceBlock)
                #
                for el, interfaceElem in enumerate(interfaceBlock):
                    dataSet[el,0] = np.uint64(maxElemId+1)
                    maxElemId = maxElemId+1
                    #
                    dataSet[el,1] = interfaceElem.ori
                    #
                    dataSet[el,2:2+noOfStructNodes] = interfaceElem.structuralNodes
                    dataSet[el,2+noOfStructNodes:] = interfaceElem.fluidNodes
                    #
            interfaceGroup.attrs['N'] = np.uint64(counter)
            # non-conform
            if self.interNodesCoords:
                comp_type = np.dtype([('Ids', 'i8'), ('xCoords', 'f8'), ('yCoords', 'f8'), ('zCoords', 'f8')])
                dataSet = interNodesGroup.create_dataset('mtxFemInterNodes', (len(self.interNodesCoords),), comp_type)
                self.interNodesCoords = np.array(self.interNodesCoords, dtype=np.float64)
                dataSet[:,'Ids'] = np.array(self.interNodesIds, dtype=np.uint64)
                dataSet[:,'xCoords'] = self.interNodesCoords[:,0]
                dataSet[:,'yCoords'] = self.interNodesCoords[:,1]
                dataSet[:,'zCoords'] = self.interNodesCoords[:,2]
            counter = 0
            for blockID, NCinterfaceBlock in enumerate(self.NCinterfaceElems):
                #
                noOfInterNodes= len(NCinterfaceBlock[0].interNodes)
                noOfStructNodes= len(NCinterfaceBlock[0].structuralNodes)
                noOfFluidNodes = len(NCinterfaceBlock[0].fluidNodes)
                #
                dataSet = NCinterfaceGroup.create_dataset('InterfaceElements' + str(blockID), data=np.zeros((len(NCinterfaceBlock), 2+noOfInterNodes+noOfStructNodes+noOfFluidNodes), dtype=np.int64)) # Cols: Id, ori, structNodes, fluidNodes
                dataSet.attrs['NinterNodes'] = np.uint64(noOfInterNodes)
                dataSet.attrs['NstructNodes'] = np.uint64(noOfStructNodes)
                dataSet.attrs['NfluidNodes'] = np.uint64(noOfFluidNodes)
                #
                structMatId = np.uint64(self.blockMaterialSelectors[NCinterfaceBlock[0].structBlockIdx].currentText())
                structMatIdx = self.blockMaterialSelectors[NCinterfaceBlock[0].structBlockIdx].currentIndex()
                dataSet.attrs['mats'] = structMatId
                #
                fluidMatId = np.uint64(self.blockMaterialSelectors[NCinterfaceBlock[0].fluidBlockIdx].currentText())
                fluidMatIdx = self.blockMaterialSelectors[NCinterfaceBlock[0].fluidBlockIdx].currentIndex()
                dataSet.attrs['matF'] = fluidMatId
                #
                if self.materials[structMatIdx].type[:7] == 'STR_LIN': 
                    if self.materials[fluidMatIdx].type[:10] == 'AF_LIN_UAF': 
                        dataSet.attrs['type'] = 'InterfaceMindlin'
                    elif self.materials[fluidMatIdx].type[:10] in ['AF_LIN_DAF', 'AF_LIN_EQF']: 
                        dataSet.attrs['type'] = 'InterfaceMindlinEquiporo'
                    else:
                        return 0
                else:
                    return 0
                #
                counter = counter + len(NCinterfaceBlock)
                #
                for el, NCinterfaceElem in enumerate(NCinterfaceBlock):
                    dataSet[el,0] = np.uint64(maxElemId+1)
                    maxElemId = maxElemId+1
                    #
                    dataSet[el,1] = NCinterfaceElem.ori
                    #
                    dataSet[el,2:2+noOfInterNodes] = NCinterfaceElem.interNodes
                    dataSet[el,2+noOfInterNodes:2+noOfInterNodes+noOfStructNodes] = NCinterfaceElem.structuralNodes
                    dataSet[el,2+noOfInterNodes+noOfStructNodes:] = NCinterfaceElem.fluidNodes
                    #
            NCinterfaceGroup.attrs['N'] = np.uint64(counter)
            return 1
        except:
            print('Error during export.')
            return 0
