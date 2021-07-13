from PyQt5.QtWidgets import QTreeWidgetItem, QPushButton, QWidget, QLabel, QMenu
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import QSize, Qt

import h5py
from standardFunctionsGeneral import readNodes, readElements, readSetup

class lev1Container(QTreeWidgetItem):
  def __init__(self, tree, hdf5File, pathToFile):
    super().__init__(tree)
    self.tree = tree
    self.pathToFile = pathToFile
    self.name = pathToFile.split('/')[-1]
    self.shortName = self.name.split('.')[0]
    # Create Widgets and add entry in tree (at level 1) of GUI
    self.createLev1TreeEntry()
    self.setExpanded(True)
    self.tree.setItemWidget(self, 0, self.lev1TreeEntry)
    # Read available data paths
    self.groupsLev2Collector = []
    self.readLev2(hdf5File)
    
  def createLev1TreeEntry(self):
    self.closeButton = QPushButton('') # construct Close-Button
    self.closeButton.setFixedSize(15,15)
    self.closeButton.setToolTip('<b>Close</b>')
    # Add widgets to line layout
    self.lev1TreeEntry = QWidget()
    self.lev1TreeEntry.setStyleSheet("QWidget {font-weight: bold;}")
    layout = QHBoxLayout()
    layout.setContentsMargins(6,6,6,6)
    self.lev1TreeEntry.setLayout(layout)
    layout.addWidget(QLabel(self.name))
    layout.addStretch(1)
    layout.addWidget(self.closeButton)
  
  def readLev2(self, hdf5File):  
    for lev2Group in hdf5File.keys(): # Level 2 loop 
      if isinstance(hdf5File[lev2Group], h5py.Group):
        if lev2Group in ['Analysis','Nodes','Elements']:
          self.groupsLev2Collector.append(lev2Container(self.tree, self, hdf5File[lev2Group], hdf5File))
   
class lev2Container(QTreeWidgetItem):
  def __init__(self, tree, parent, lev2Group, hdf5File):
    super().__init__(parent)
    self.tree = tree
    self.fullPath = lev2Group.name
    self.name = self.fullPath.split('/')[-1]
    # Create Widgets and add entry in tree (at level 2) of GUI
    self.createLev2TreeEntry()
    # Read available data sets or information
    self.dataSetsLev3Collector = []
    if self.name == 'Analysis':
      self.setExpanded(True)
      self.fillAnalysis(hdf5File)
    elif self.name == 'Nodes':
      self.fillNodes(hdf5File)
    elif self.name == 'Elements':
      self.fillElements(hdf5File)
    else:
      pass
    self.tree.setItemWidget(self, 0, self.lev2TreeEntry)
        
  def createLev2TreeEntry(self):
    self.lev2TreeEntry = QWidget()
    layout = QHBoxLayout()
    layout.setContentsMargins(0,0,0,0)
    self.lev2TreeEntry.setLayout(layout)
    layout.addWidget(QLabel(self.name.split('/')[-1])) 
    layout.addStretch(1)
  
  def fillAnalysis(self, hdf5File):
    readSetup(self.lev2TreeEntry, hdf5File)
    self.dataSetsLev3Collector.append(lev3ContainerInfo(self.tree, self, ['ID: ' + str(self.lev2TreeEntry.analysisID),
                                                                          'Type: ' + str(self.lev2TreeEntry.analysisType),
                                                                          'Frequency start: ' + str(self.lev2TreeEntry.freqStart), 
                                                                          'Frequency steps: ' + str(self.lev2TreeEntry.freqSteps), 
                                                                          'Frequency delta: ' + str(self.lev2TreeEntry.freqDelta), 
                                                                          'Description: ' + str(self.lev2TreeEntry.description)]))

  def fillNodes(self, hdf5File):
    self.lev2TreeEntry.nodeSets = []
    readNodes(self.lev2TreeEntry, hdf5File)
    self.dataSetsLev3Collector.append(lev3ContainerNodes(self.tree, self, self.lev2TreeEntry.nodes))
    
  def fillElements(self, hdf5File):
    self.lev2TreeEntry.elems = []
    self.lev2TreeEntry.elementSets = []
    readElements(self.lev2TreeEntry, hdf5File)
    self.dataSetsLev3Collector.append(lev3ContainerElements(self.tree, self, self.lev2TreeEntry.elems))
  
class lev3ContainerInfo(QTreeWidgetItem):
  def __init__(self, tree, parent, info):
    super().__init__(parent)
    self.tree = tree
    # Create Widgets and add entry in tree (at level 3 / dataSet level) of GUI
    self.createDataSetTreeEntryInfo(info)
    self.tree.setItemWidget(self, 0, self.DataSetTreeEntry)
    
  def createDataSetTreeEntryInfo(self, info):
    self.DataSetTreeEntry = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    self.DataSetTreeEntry.setLayout(layout)
    for line in info:
      layout.addWidget(QLabel(line))
      
class lev3ContainerNodes(QTreeWidgetItem):
  def __init__(self, tree, parent, nodes):
    super().__init__(parent)
    self.tree = tree
    # Create Widgets and add entry in tree (at level 3 / dataSet level) of GUI
    self.createDataSetTreeEntryNodeSet(nodes)
    self.tree.setItemWidget(self, 0, self.DataSetTreeEntry)
    
  def createDataSetTreeEntryNodeSet(self, nodes):
    self.DataSetTreeEntry = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    self.DataSetTreeEntry.setLayout(layout)
    layout.addWidget(QLabel('#Nodes: ' + str(len(nodes))))

class lev3ContainerElements(QTreeWidgetItem):
  def __init__(self, tree, parent, elems):
    super().__init__(parent)
    self.tree = tree
    # Create Widgets and add entry in tree (at level 3 / dataSet level) of GUI
    self.createDataSetTreeEntryElemSet(elems)
    self.tree.setItemWidget(self, 0, self.DataSetTreeEntry)
    
  def createDataSetTreeEntryElemSet(self, elems):
    self.DataSetTreeEntry = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    self.DataSetTreeEntry.setLayout(layout)
    for block in elems:
      layout.addWidget(QLabel('Block ' + str(block.attrs['Id']) + ' | ' + str(len(block)) + ' ' + str(block.attrs['ElementType']) + ' elements\nMaterial ' + str(block.attrs['MaterialId'])))

class lev3ContainerField(QTreeWidgetItem):
  def __init__(self, tree, parent, hdf5ResultsFileStateGroup, field, fieldIndices, nodeIndices, frequencies):
    super().__init__(parent)
    self.tree = tree
    self.hdf5ResultsFileStateGroup = hdf5ResultsFileStateGroup
    self.field = field
    self.fieldIndices = fieldIndices
    self.nodeIndices = nodeIndices
    self.frequencies = frequencies
    # Create Widgets and add entry in tree (at level 3 / dataSet level) of GUI
    self.createDataSetTreeEntryField(field)
    self.tree.setItemWidget(self, 0, self.DataSetTreeEntry)
    
  def createDataSetTreeEntryField(self, field):
    self.DataSetTreeEntry = QWidget()
    layout = QVBoxLayout()
    layout.setSpacing(0)
    layout.setContentsMargins(0,0,0,0)
    self.DataSetTreeEntry.setLayout(layout)
    layout.addWidget(QLabel(field))

class lev3Container(QTreeWidgetItem):
  def __init__(self, tree, parent, DataSet):
    super().__init__(parent)
    self.tree = tree
    self.fullPath = DataSet.name
    self.name = self.fullPath.split('/')[-1]
    # Create Widgets and add entry in tree (at level 3 / dataSet level) of GUI
    self.createDataSetTreeEntry(parent.name)
    self.tree.setItemWidget(self, 0, self.DataSetTreeEntry)
  
  def createDataSetTreeEntry(self, myType):
    self.DataSetTreeEntry = QWidget()
    layout = QHBoxLayout()
    self.DataSetTreeEntry.setLayout(layout)
    layout.addWidget(QLabel(self.name))
    # Select method according to type
    if myType == 'Geometry':
      self.createDataSetTreeEntryInGeometry(layout)
    elif myType == 'Analysis':
      self.createDataSetTreeEntryInSetup(layout)
    elif myType == 'Results':
      self.createDataSetTreeEntryInResult(layout)
    else: 
      self.createDataSetTreeEntryUndefined(layout)
    layout.addStretch(1)
  
  def createDataSetTreeEntryInGeometry(self, layout):
    pass
    
  def createDataSetTreeEntryInSetup(self, layout):
    pass
    
  def createDataSetTreeEntryInResult(self, layout):
    pass
    
  def createDataSetTreeEntryUndefined(self, layout):
    layout.itemAt(0).widget().setText(self.name + ' [undefined]') 
    layout.itemAt(0).widget().adjustSize()
    
  def loadRequestedDataToMemory(self):
    print('Hello')
    
  def releaseData(self):
    pass