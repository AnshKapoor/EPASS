# Modules
import os
import h5py
import atexit
import numpy as np
from DataStructure import lev1Container, lev2Container, lev3ContainerNodes, lev3ContainerElements, lev3ContainerField
from PyQt5.QtWidgets import QFileDialog, QMenu, QAction
#from PyQt5.QtCore import 
from PyQt5.QtGui import QCursor
from standardFunctionsGeneral import getFieldIndices
from standardModules import calcMeanSquared

class Controller():
  def __init__(self, inaGui):
    self.inaGui = inaGui
    self.vtkWindow = inaGui.vtkWindow
    self.graphWindow = inaGui.graphWindow
    self.graphWindow.fig.canvas.mpl_connect('button_press_event', self.graphWindowClick)
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
    self.cmenuSolution = QMenu(self.inaGui)
    self.drawActSolutionMean = self.cmenuSolution.addAction("Draw mean squared value")
    #
    [x.setStyleSheet("QMenu::item:selected { background: #abc13b; }") for x in [self.cmenuAllNodes, self.cmenuBlock, self.cmenuAllBlocks, self.cmenuSolution]]
      
  def loadFile(self):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(self.inaGui,"QFileDialog.getOpenFileName()", "","hdf5 file (*.hdf5)", options=options)
    if fileName:
      fileEnding = fileName.split('.')[-1]
      if fileEnding in ['hdf5']:
        self.loadHdf5(fileName)
                
  def loadHdf5(self, pathToFile):
    with h5py.File(pathToFile, 'r') as hdf5File:
      self.groupsLev1Collector.append(lev1Container(self.tree, hdf5File, pathToFile))
      self.init2DAxes(self.groupsLev1Collector[-1])
      allLev2Names = [lev2Entry.name for lev2Entry in self.groupsLev1Collector[-1].groupsLev2Collector]
      if 'Nodes' in allLev2Names and 'Elements' in allLev2Names:
        nodeEntry = self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry
        elemEntry = self.groupsLev1Collector[-1].groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry
        self.create3DRepresentation(nodeEntry, elemEntry)
        myPath = '/'.join(pathToFile.split('/')[:-1])
        myFile = pathToFile.split('/')[-1]
        pathToResultsFile = myPath + '/eGenOutput_' + myFile
        if os.path.isfile(pathToResultsFile):
          hdf5ResultsFile = h5py.File(pathToResultsFile, 'r')
          hdf5ResultsFileStateGroup = hdf5ResultsFile['Solution/State']
          atexit.register(hdf5ResultsFile.close)
          self.groupsLev1Collector[-1].groupsLev2Collector.append(lev2Container(self.tree, self.groupsLev1Collector[-1], hdf5ResultsFile['Solution'], hdf5ResultsFile))
          fields, fieldIndices = getFieldIndices(nodeEntry.nodes, nodeEntry.nodesInv, elemEntry.elems)
          for field, fieldIdx in zip(fields, fieldIndices):
            self.groupsLev1Collector[-1].groupsLev2Collector[-1].dataSetsLev3Collector.append(lev3ContainerField(self.tree, self.groupsLev1Collector[-1].groupsLev2Collector[-1], hdf5ResultsFileStateGroup, field, fieldIdx))
      self.connectButtons(self.groupsLev1Collector[-1])
      
  def create3DRepresentation(self, nodeEntry, elemEntry):
    [nodeEntry.nodeActor, elemEntry.blockActors, elemEntry.blockEdgeActors] = self.vtkWindow.createGrid(nodeEntry.nodes, nodeEntry.nodesInv, elemEntry.elems)
    
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
      action = self.cmenuSolution.exec_(QCursor.pos())
    if action == self.drawActSolutionMean:
      x,y = calcMeanSquared(item.hdf5ResultsFileStateGroup, item.fieldIndices, 1, 1.)
      self.graphWindow.plot(x,y,item.field + ' (' + item.parent().parent().shortName + ')')
            
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

  def graphWindowClick(self, event):
    if event.xdata:
      self.vtkWindow.currentFrequency = event.xdata
      self.vtkWindow.updateNumber()
      self.graphWindow.currentFrequency = event.xdata
      self.graphWindow.updateFrequencySelector()
      