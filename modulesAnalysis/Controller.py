# Modules
import os
import h5py
import numpy as np
from DataStructure import lev1Container, lev2Container, lev3ContainerNodes, lev3ContainerElements
from PyQt5.QtWidgets import QFileDialog, QMenu, QAction
#from PyQt5.QtCore import 
from PyQt5.QtGui import QCursor

class Controller():
  def __init__(self, inaGui):
    self.inaGui = inaGui
    self.vtkWindow = inaGui.vtkWindow
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
    #
    [x.setStyleSheet("QMenu::item:selected { background: #abc13b; }") for x in [self.cmenuAllNodes, self.cmenuBlock, self.cmenuAllBlocks]]
      
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
      self.create3DRepresentation(self.groupsLev1Collector[-1])
      self.connectButtons(self.groupsLev1Collector[-1])
    
  def create3DRepresentation(self, groupLev1):
    allLev2Names = [lev2Entry.name for lev2Entry in groupLev1.groupsLev2Collector]
    if 'Nodes' in allLev2Names and 'Elements' in allLev2Names:
      nodeEntry = groupLev1.groupsLev2Collector[allLev2Names.index('Nodes')].lev2TreeEntry
      elemEntry = groupLev1.groupsLev2Collector[allLev2Names.index('Elements')].lev2TreeEntry
      [nodeEntry.nodeActor, elemEntry.blockActors, elemEntry.blockEdgeActors] = self.vtkWindow.createGrid(nodeEntry.nodes, nodeEntry.nodesInv, elemEntry.elems)
    
  def connectButtons(self,currentLev1Container):
    currentLev1Container.closeButton.clicked.connect(self.removeLev1Entry)
    for currentLev2Container in currentLev1Container.groupsLev2Collector:
      for currentLev3Container in currentLev2Container.dataSetsLev3Collector:
        pass
        #currentLev3Container.drawButton.clicked.connect(self.drawData)

  def removeLev1Entry(self):
    closeButtonWhichSentSignal = self.inaGui.sender()
    indexOfLev1EntryToBeRemoved = [x.closeButton for x in self.groupsLev1Collector].index(closeButtonWhichSentSignal)
    self.tree.takeTopLevelItem(indexOfLev1EntryToBeRemoved)
    self.groupsLev1Collector.pop(indexOfLev1EntryToBeRemoved)
    
  def treeWidgetItemClick(self, pos):
    item=self.tree.currentItem()
    item1= self.tree.itemAt(pos)
    if isinstance(item, lev2Container):
      if item.name == 'Nodes':
        action = self.cmenuAllNodes.exec_(QCursor.pos())
      if item.name == 'Elements':
        action = self.cmenuAllBlocks.exec_(QCursor.pos())
    if isinstance(item, lev3ContainerNodes):
      action = self.cmenuAllNodes.exec_(QCursor.pos())
    if isinstance(item, lev3ContainerElements):
      action = self.cmenuBlock.exec_(QCursor.pos())
            
  def drawData(self):
    drawButtonWhichSentSignal = self.inaGui.sender()
    for currentLev1Container in self.groupsLev1Collector:
      for currentLev2Container in currentLev1Container.groupsLev2Collector:
        indexOfLev3Entry = [x.drawButton for x in currentLev2Container.dataSetsLev3Collector].index(drawButtonWhichSentSignal)
        dataSet = currentLev2Container.dataSetsLev3Collector[indexOfLev3Entry]
        dataSet.loadRequestedDataToMemory()
        #
        dataSet.releaseData()
        