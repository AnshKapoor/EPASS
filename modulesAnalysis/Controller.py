# Modules
import os
import h5py
import atexit
import numpy as np
from DataStructure import lev1Container, lev2Container, lev3ContainerNodes, lev3ContainerElements, lev3ContainerField
from PyQt5.QtWidgets import QFileDialog, QMenu, QAction, QCheckBox, QHBoxLayout, QLabel, QLineEdit, QButtonGroup
from matplotlib.backend_bases import MouseButton
from matplotlib import pyplot as plt
#from PyQt5.QtCore import 
from PyQt5.QtGui import QCursor
from standardFunctionsGeneral import getFieldIndices, isPlateType, isFluid3DType, isStructure3DType, getElementDof
from standardWidgets import messageboxOK
from standardModules import calcMeanSquared, calcSoundPower, setupRayleighWindow

class Controller():
  def __init__(self, inaGui):
    self.inaGui = inaGui
    self.vtkWindow = inaGui.vtkWindow
    self.vtkWindow.customContextMenuRequested.connect(self.vtkRightClick)
    self.graphWindow = inaGui.graphWindow
    self.graphWindow.fig.canvas.mpl_connect('button_press_event', self.graphWindowClick)
    self.graphWindow.customContextMenuRequested.connect(self.graphRightClick)
    self.tree = self.inaGui.dataTree
    self.tree.customContextMenuRequested.connect(self.treeWidgetItemClick)
    # Connectors 
    self.inaGui.loadAct.triggered.connect(self.loadFile)
    # Submenus
    self.initSubMenus()
    # List of loaded level 1 groups
    self.groupsLev1Collector = []
    # Dummycode which must be addressed by button later
    #self.loadHdf5('example.hdf5')
    #
    self.currentPlot = 0
  
  def initSubMenus(self):
    # All nodes
    self.cmenuAllNodes = QMenu(self.inaGui)
    self.drawActNodes = self.cmenuAllNodes.addAction("Draw all nodes")
    self.highlightActNodes = self.cmenuAllNodes.addAction("Highlight all nodes")
    # Blocks
    self.cmenuBlock = QMenu(self.inaGui)
    self.drawActBlock = self.cmenuBlock.addAction("Draw block")
    self.highlightActBlock = self.cmenuBlock.addAction("Highlight block")
    # All blocks
    self.cmenuAllBlocks = QMenu(self.inaGui)
    self.drawActAllBlocks = self.cmenuAllBlocks.addAction("Draw all blocks")
    # Results
    self.cmenuSolutionPres = QMenu(self.inaGui)
    self.drawActSolutionPresMean = self.cmenuSolutionPres.addAction("Mean squared value")
    self.cmenuSolutionDisp = QMenu(self.inaGui)
    self.drawActSolutionDispMean = self.cmenuSolutionDisp.addAction("Mean squared value")
    self.drawActSolutionDispMeanVelo = self.cmenuSolutionDisp.addAction("Mean squared velocity")
    self.drawActSolutionDispSoundPower = self.cmenuSolutionDisp.addAction("Radiated sound power")
    self.drawActSolutionDispRadiationEfficiency = self.cmenuSolutionDisp.addAction("Radiation efficiency")
    self.drawActSolutionDispTransmissionLoss = self.cmenuSolutionDisp.addAction("Transmission loss")
    self.cmenuSolutionRot = QMenu(self.inaGui)
    self.drawActSolutionRotMean = self.cmenuSolutionRot.addAction("Mean squared value")
    # 3D options
    self.cmenuVTK = QMenu(self.inaGui)
    self.vtkActReset = self.cmenuVTK.addAction("Reset view")
    self.vtkActAxes = self.cmenuVTK.addAction("Show axes")
    self.vtkActAxes.setCheckable(1)
    self.vtkActAxes.setChecked(1)
    self.vtkActNodes = self.cmenuVTK.addAction("Show nodes")
    self.vtkActNodes.setCheckable(1)
    self.vtkActNodes.setChecked(1)
    self.vtkActColor = self.cmenuVTK.addAction("Change background color")
    self.vtkActColor.setCheckable(0)
    #self.vtkActWarp = self.cmenuVTK.addAction("Warp")
    #self.vtkActWarp.setCheckable(1)
    # 2D options
    self.cmenuGraph = QMenu(self.inaGui)
    self.vtkActSave = self.cmenuGraph.addAction("Save")
    #
    [x.setStyleSheet("QMenu::item:selected { background: #abc13b; }") for x in [self.cmenuAllNodes, self.cmenuBlock, self.cmenuAllBlocks, self.cmenuSolutionPres, self.cmenuSolutionDisp, self.cmenuSolutionRot, self.cmenuVTK, self.cmenuGraph]]
      
  def loadFile(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(self.inaGui,"QFileDialog.getOpenFileName()", "","hdf5 file (*.hdf5)", options=options)
    if fileName:
      fileEnding = fileName.split('.')[-1]
      if fileEnding in ['hdf5']:
        self.loadHdf5(fileName)
                
  def loadHdf5(self, pathToFile):
    hdf5File = h5py.File(pathToFile, 'r')
    atexit.register(hdf5File.close)
    self.groupsLev1Collector.append(lev1Container(self.tree, hdf5File, pathToFile))
    self.init2DAxes(self.groupsLev1Collector[-1])
    allLev2Names = [lev2Entry.name for lev2Entry in self.groupsLev1Collector[-1].groupsLev2Collector]
    if 'Nodes' in allLev2Names and 'Elements' in allLev2Names:
      nodeEntry = self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry
      elemEntry = self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry
      self.create3DRepresentation(nodeEntry, elemEntry)
      #myDict = dict(sorted(nodeEntry.nodesInv.items(), key=lambda item: item[0]))
      #nodeEntry.orderIdx = [item[1] for item in myDict.items()]
      #nodeEntry.orderIdx2 = [item[1] for item in nodeEntry.nodesInv.items()]
      #print(nodeEntry.orderIdx2)
      myPath = '/'.join(pathToFile.split('/')[:-1])
      myFile = pathToFile.split('/')[-1]
      pathToResultsFile = myPath + '/eGenOutput_' + myFile
      if os.path.isfile(pathToResultsFile):
        hdf5ResultsFile = h5py.File(pathToResultsFile, 'r')
        hdf5ResultsFileStateGroup = hdf5ResultsFile['Solution/State']
        atexit.register(hdf5ResultsFile.close)
        self.groupsLev1Collector[-1].groupsLev2Collector.append(lev2Container(self.tree, self.groupsLev1Collector[-1], hdf5ResultsFile['Solution'], hdf5ResultsFile))
        fields, fieldIndices, nodeIndices, nodeEntry.startIdxPerNode = getFieldIndices(nodeEntry.nodes, nodeEntry.orderIdx, nodeEntry.nodesInv, elemEntry.elems)
        for n in range(len(fields)):
          self.groupsLev1Collector[-1].groupsLev2Collector[-1].dataSetsLev3Collector.append(lev3ContainerField(self.tree, self.groupsLev1Collector[-1].groupsLev2Collector[-1], hdf5ResultsFileStateGroup, fields[n], fieldIndices[n], nodeIndices[n], self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Analysis')].lev2TreeEntry.frequencies))
        self.initSetupWindows()
    self.connectButtons(self.groupsLev1Collector[-1])

  def initSetupWindows(self):
    # mean
    self.blockCheckerMean = []
    self.setupWindowMean = setupRayleighWindow()
    self.setupWindowMean.layout.addRow(QLabel('Select block.'), QLabel(' '))
    allLev2Names = [lev2Entry.name for lev2Entry in self.groupsLev1Collector[-1].groupsLev2Collector]
    self.buttonGroupMean = QButtonGroup()
    for buttonIdx, block in enumerate(self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry.elems):
      self.blockCheckerMean.append(QCheckBox())
      self.buttonGroupMean.addButton(self.blockCheckerMean[-1], buttonIdx)
      subLayout = QHBoxLayout()
      [subLayout.addWidget(wid) for wid in [self.blockCheckerMean[-1], QLabel('Block ' + str(block.attrs['Id']) + ' (' + str(block.attrs['ElementType']) + ')')]]
      subLayout.addStretch()
      self.setupWindowMean.blockLayout.addLayout(subLayout)
    self.setupWindowMean.blockLayout.addStretch()
    # Rayleigh
    self.blockCheckerRayleigh = []
    self.setupWindowRayleigh = setupRayleighWindow()
    self.setupWindowRayleigh.speedOfSound = QLineEdit('341.')
    self.setupWindowRayleigh.density = QLineEdit('1.21')
    self.setupWindowRayleigh.layout.addRow(QLabel('Speed of sound'), self.setupWindowRayleigh.speedOfSound)
    self.setupWindowRayleigh.layout.addRow(QLabel('Density'), self.setupWindowRayleigh.density)
    allLev2Names = [lev2Entry.name for lev2Entry in self.groupsLev1Collector[-1].groupsLev2Collector]
    self.buttonGroupRayleigh = QButtonGroup()
    for buttonIdx, block in enumerate(self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry.elems):
      self.blockCheckerRayleigh.append(QCheckBox())
      self.buttonGroupRayleigh.addButton(self.blockCheckerRayleigh[-1], buttonIdx)
      if not isPlateType(str(block.attrs['ElementType'])):
        self.blockCheckerRayleigh[-1].setEnabled(False)
      subLayout = QHBoxLayout()
      [subLayout.addWidget(wid) for wid in [self.blockCheckerRayleigh[-1], QLabel('Block ' + str(block.attrs['Id']) + ' (' + str(block.attrs['ElementType']) + ')')]]
      subLayout.addStretch()
      self.setupWindowRayleigh.blockLayout.addLayout(subLayout)
    self.setupWindowRayleigh.blockLayout.addStretch()
    # Rayleigh for Transmission Loss
    self.blockCheckerTL = []
    self.setupWindowTL = setupRayleighWindow()
    self.setupWindowTL.speedOfSound = QLineEdit('341.')
    self.setupWindowTL.density = QLineEdit('1.21')
    self.setupWindowTL.inputPower = QLineEdit('1.')
    self.setupWindowTL.layout.addRow(QLabel('Speed of sound'), self.setupWindowTL.speedOfSound)
    self.setupWindowTL.layout.addRow(QLabel('Density'), self.setupWindowTL.density)
    self.setupWindowTL.layout.addRow(QLabel('Input power (sender room)'), self.setupWindowTL.inputPower)
    allLev2Names = [lev2Entry.name for lev2Entry in self.groupsLev1Collector[-1].groupsLev2Collector]
    self.buttonGroupTL = QButtonGroup()
    for buttonIdx, block in enumerate(self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry.elems):
      self.blockCheckerTL.append(QCheckBox())
      self.buttonGroupTL.addButton(self.blockCheckerTL[-1], buttonIdx)
      if not isPlateType(str(block.attrs['ElementType'])):
        self.blockCheckerTL[-1].setEnabled(False)
      subLayout = QHBoxLayout()
      [subLayout.addWidget(wid) for wid in [self.blockCheckerTL[-1], QLabel('Block ' + str(block.attrs['Id']) + ' (' + str(block.attrs['ElementType']) + ')')]]
      subLayout.addStretch()
      self.setupWindowTL.blockLayout.addLayout(subLayout)
    self.setupWindowTL.blockLayout.addStretch()

  def create3DRepresentation(self, nodeEntry, elemEntry):
    [nodeEntry.blockGrids, nodeEntry.orderIdx, nodeEntry.nodeActor, elemEntry.blockActors, elemEntry.blockEdgeActors] = self.vtkWindow.createGrid(nodeEntry.nodes, nodeEntry.nodesInv, elemEntry.elems)

  def fieldTo3DRepresentation(self, dataSetEntry):
    nearestFrequencyIdx = np.argmin(np.abs(np.array(dataSetEntry.frequencies)-float(self.graphWindow.currentFrequency)))
    self.vtkWindow.currentFrequency = dataSetEntry.frequencies[nearestFrequencyIdx]
    self.vtkWindow.updateNumber()
    self.graphWindow.currentFrequency = dataSetEntry.frequencies[nearestFrequencyIdx]
    self.graphWindow.updateFrequencySelector()
    #
    for item in dataSetEntry.hdf5ResultsFileStateGroup.attrs.items():
      if abs(float(item[1])-float(self.vtkWindow.currentFrequency))<0.01:
        allLev2Names = [lev2Entry.name for lev2Entry in dataSetEntry.parent().parent().groupsLev2Collector]
        #
        dataSet = dataSetEntry.hdf5ResultsFileStateGroup['vecFemStep' + str(int(item[0][8:]))]
        #
        boolIdx = np.zeros((len(dataSet)), dtype=np.bool_)
        boolIdx[dataSetEntry.fieldIndices] = 1
        #
        myArray = np.zeros((len(dataSetEntry.parent().parent().groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry.nodes)), dtype=complex)
        myArray.real[dataSetEntry.nodeIndices] = dataSet['real'][boolIdx]
        myArray.imag[dataSetEntry.nodeIndices] = dataSet['imag'][boolIdx]
        #
        grids = dataSetEntry.parent().parent().groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry.blockGrids
        mappers = [blockActor.GetMapper() for blockActor in dataSetEntry.parent().parent().groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry.blockActors]
        self.vtkWindow.colorplot(np.abs(myArray), dataSetEntry.field, grids, mappers, 0)
        #if self.vtkActWarp.isChecked():
        #  self.vtkWindow.colorplot(np.abs(myArray), dataSetEntry.field, grid, mapper, 1)
        #else:
        #  self.vtkWindow.colorplot(np.abs(myArray), dataSetEntry.field, grid, mapper, 0)
                            
  def connectButtons(self,currentLev1Container):
    currentLev1Container.closeButton.clicked.connect(self.removeLev1Entry)
    #for currentLev2Container in currentLev1Container.groupsLev2Collector:
    #  for currentLev3Container in currentLev2Container.dataSetsLev3Collector:
    #    pass

  def removeLev1Entry(self):
    closeButtonWhichSentSignal = self.inaGui.sender()
    indexOfLev1EntryToBeRemoved = [x.closeButton for x in self.groupsLev1Collector].index(closeButtonWhichSentSignal)
    self.tree.takeTopLevelItem(indexOfLev1EntryToBeRemoved)
    self.groupsLev1Collector.pop(indexOfLev1EntryToBeRemoved)
    
  def treeWidgetItemClick(self, pos):
    item=self.tree.currentItem()
    #item1= self.tree.itemAt(pos)
    action = 0
    #if isinstance(item, lev2Container):
    #  if item.name == 'Nodes':
    #    action = self.cmenuAllNodes.exec_(QCursor.pos())
    #  if item.name == 'Elements':
    #    action = self.cmenuAllBlocks.exec_(QCursor.pos())
    #if isinstance(item, lev3ContainerNodes):
    #  action = self.cmenuAllNodes.exec_(QCursor.pos())
    #if isinstance(item, lev3ContainerElements):
    #  action = self.cmenuBlock.exec_(QCursor.pos())
    if isinstance(item, lev3ContainerField):
      if 'sound pressure' in item.field:
        action = self.cmenuSolutionPres.exec_(QCursor.pos())
      elif 'displacement' in item.field:
        action = self.cmenuSolutionDisp.exec_(QCursor.pos())
      elif 'rotation' in item.field:
        action = self.cmenuSolutionRot.exec_(QCursor.pos())
    ###
    if action == self.drawActSolutionDispMean or action == self.drawActSolutionRotMean or action == self.drawActSolutionPresMean:
      var = self.setupWindowMean.exec_()
      if var == 0: 
        pass
      elif var == 1: 
        allLev2Names = [lev2Entry.name for lev2Entry in item.parent().parent().groupsLev2Collector]
        nodeEntry = item.parent().parent().groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry
        elemEntry = item.parent().parent().groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry
        #
        elemType = str(elemEntry.elems[self.buttonGroupMean.checkedId()].attrs['ElementType'])
        if item.field in getElementDof(elemType):
          if isFluid3DType(elemType) or isStructure3DType(elemType):
            noOfNodesPerElem = 8
          else:
            noOfNodesPerElem = 4
          x,y = calcMeanSquared(item.hdf5ResultsFileStateGroup, item.fieldIndices, nodeEntry.nodes, nodeEntry.nodesInv, nodeEntry.orderIdx, nodeEntry.startIdxPerNode, elemEntry.elems[self.buttonGroupMean.checkedId()], noOfNodesPerElem)
          if all(y): 
            y = 10*np.log10(y)
            yLabel = 'Mean squared ' + str(item.field) + ' [dB ref 1.]'
          else:
            yLabel = 'Mean squared ' + str(item.field)
          self.graphWindow.plot(x,y,item.parent().parent().shortName)
          self.graphWindow.setLabels('Frequency [Hz]', yLabel)
          self.currentPlot = item
          self.fieldTo3DRepresentation(item)
        else:
          messageboxOK('Error', 'Field not available in chosen block!')
    if action == self.drawActSolutionDispMeanVelo:
      var = self.setupWindowMean.exec_()
      if var == 0: 
        pass
      elif var == 1: 
        allLev2Names = [lev2Entry.name for lev2Entry in item.parent().parent().groupsLev2Collector]
        nodeEntry = item.parent().parent().groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry
        elemEntry = item.parent().parent().groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry
        #
        elemType = str(elemEntry.elems[self.buttonGroupMean.checkedId()].attrs['ElementType'])
        if item.field in getElementDof(elemType):
          if isFluid3DType(str(elemEntry.elems[self.buttonGroupMean.checkedId()].attrs['ElementType'])) or isStructure3DType(str(elemEntry.elems[self.buttonGroupMean.checkedId()].attrs['ElementType'])):
            noOfNodesPerElem = 8
          else:
            noOfNodesPerElem = 4
          x,y = calcMeanSquared(item.hdf5ResultsFileStateGroup, item.fieldIndices, nodeEntry.nodes, nodeEntry.nodesInv, nodeEntry.orderIdx, nodeEntry.startIdxPerNode, elemEntry.elems[self.buttonGroupMean.checkedId()], noOfNodesPerElem, 1)
          if all(y): 
            y = 10*np.log10(y)
            yLabel = 'Mean squared velocity [dB ref 1.]'
          else:
            yLabel = 'Mean squared velocity'
          self.graphWindow.plot(x,y,item.parent().parent().shortName)
          self.graphWindow.setLabels('Frequency [Hz]', yLabel)
          self.currentPlot = item
          self.fieldTo3DRepresentation(item)
        else:
          messageboxOK('Error', 'Field not available in chosen block!')
    if action in [self.drawActSolutionDispSoundPower, self.drawActSolutionDispRadiationEfficiency, self.drawActSolutionDispTransmissionLoss]:
      if action in [self.drawActSolutionDispSoundPower, self.drawActSolutionDispRadiationEfficiency]:
        try: 
          var = self.setupWindowRayleigh.exec_()
          speedOfSound = float(self.setupWindowRayleigh.speedOfSound.text())
          density = float(self.setupWindowRayleigh.density.text())
        except: 
          messageboxOK('Error', 'User input for speed of sound and density \n cannot be converted to float!')
          var = 0
      if action == self.drawActSolutionDispTransmissionLoss:
        try: 
          var = self.setupWindowTL.exec_()
          speedOfSound = float(self.setupWindowTL.speedOfSound.text())
          density = float(self.setupWindowTL.density.text())
          inputPower = float(self.setupWindowTL.inputPower.text())
        except: 
          messageboxOK('Error', 'User input for speed of sound and density \n cannot be converted to float!')
          var = 0
      #
      if var == 0: 
        pass
      elif var == 1: 
        allLev2Names = [lev2Entry.name for lev2Entry in item.parent().parent().groupsLev2Collector]
        nodeEntry = item.parent().parent().groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry
        elemEntry = item.parent().parent().groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry
        x,ySoundPower,ySigma = calcSoundPower(item.hdf5ResultsFileStateGroup, item.fieldIndices, nodeEntry.nodes, nodeEntry.nodesInv, nodeEntry.orderIdx, nodeEntry.startIdxPerNode, elemEntry.elems[self.buttonGroupRayleigh.checkedId()], speedOfSound, density)
        if action == self.drawActSolutionDispSoundPower: 
          if all(ySoundPower): 
            y = 10*np.log10(ySoundPower)
          else: 
            y = ySoundPower
          yLabel = 'Sound power [dB ref 1.]'
        elif action == self.drawActSolutionDispRadiationEfficiency:
          y = ySigma
          yLabel = 'Radiation efficiency [-]'
        elif action == self.drawActSolutionDispTransmissionLoss:
          if all(ySoundPower): 
            y = 10*np.log10(np.divide(inputPower, ySoundPower))
          else: 
            y = inputPower
          yLabel = 'Transmission loss [dB]'
        self.graphWindow.plot(x,y,item.parent().parent().shortName)
        self.graphWindow.setLabels('Frequency [Hz]', yLabel)
        self.currentPlot = item
        self.fieldTo3DRepresentation(item)

  def vtkRightClick(self):
    action = self.cmenuVTK.exec_(QCursor.pos())
    if action == self.vtkActReset:
      self.vtkWindow.resetView()
    elif action == self.vtkActAxes:
      if self.vtkActAxes.isChecked():
        self.vtkWindow.axisEnable()
      else:
        self.vtkWindow.axisDisable()
    elif action == self.vtkActNodes:
      if self.vtkActNodes.isChecked():
        self.vtkWindow.nodesEnable()
      else:
        self.vtkWindow.nodesDisable()
    elif action == self.vtkActColor:
      self.vtkWindow.changeBackgroundColor()
    #elif action == self.vtkActWarp:
    #  if self.currentPlot: 
    #      self.fieldTo3DRepresentation(self.currentPlot)

  def graphRightClick(self):
    action = self.cmenuGraph.exec_(QCursor.pos())
    if action == self.vtkActSave:
      options = QFileDialog.Options()
      options |= QFileDialog.DontUseNativeDialog
      fileName, fileEnding = QFileDialog.getSaveFileName(self.inaGui,"QFileDialog.getSaveFileName()","","Picture (*.png);;Text File (*.txt)", options=options)
      if fileEnding == 'Text File (*.txt)':
        if not fileName[-4:] == '.txt':
          fileName += ".txt";
        self.graphWindow.saveDataAscii(fileName)
      else: 
        if not fileName[-4:] == '.png':
          fileName += '.png';
        self.graphWindow.saveDataPicture(fileName)

  def drawData(self):
    drawButtonWhichSentSignal = self.inaGui.sender()
    for currentLev1Container in self.groupsLev1Collector:
      for currentLev2Container in currentLev1Container.groupsLev2Collector:
        indexOfLev3Entry = [x.drawButton for x in currentLev2Container.dataSetsLev3Collector].index(drawButtonWhichSentSignal)
        dataSet = currentLev2Container.dataSetsLev3Collector[indexOfLev3Entry]
        dataSet.loadRequestedDataToMemory()
        #
        dataSet.releaseData()
        
  def init2DAxes(self, groupLev1):
    allLev2Names = [lev2Entry.name for lev2Entry in groupLev1.groupsLev2Collector]
    if 'Analysis' in allLev2Names:
      freqs = groupLev1.groupsLev2Collector[allLev2Names.index('Analysis')].lev2TreeEntry.frequencies
      self.graphWindow.setAxesLimits([min(freqs), max(freqs)], [0, 1])
      self.graphWindow.currentFrequency = (min(freqs) + max(freqs)) / 2.
      self.graphWindow.updateFrequencySelector()

  def graphWindowClick(self, event):
    if event.xdata and event.button == MouseButton.LEFT:
      self.vtkWindow.currentFrequency = event.xdata
      self.vtkWindow.updateNumber()
      self.graphWindow.currentFrequency = event.xdata
      self.graphWindow.updateFrequencySelector()
      if self.currentPlot: 
        self.fieldTo3DRepresentation(self.currentPlot)
      