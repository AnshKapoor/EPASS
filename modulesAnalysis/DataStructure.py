from PyQt5.QtWidgets import QTreeWidgetItem, QPushButton, QWidget, QLabel
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtCore import QSize, Qt

import h5py

class lev1Container(QTreeWidgetItem):
  def __init__(self, tree, hdf5File, pathToFile):
    super().__init__(tree)
    self.tree = tree
    self.pathToFile = pathToFile
    self.name = pathToFile.split('/')[-1]
    # Create Widgets and add entry in tree (at level 1) of GUI
    self.createLev1TreeEntry()
    self.tree.setItemWidget(self, 0, self.lev1TreeEntry)
    # Read available data paths
    self.groupsLev2Collector = []
    #self.readLev2(hdf5File)
    
  def createLev1TreeEntry(self):
    self.closeButton = QPushButton('') # construct Close-Button
    self.closeButton.setFixedSize(15,15)
    self.closeButton.setToolTip('<b>Close</b>')
    # Add widgets to line layout
    self.lev1TreeEntry = QWidget()
    layout = QHBoxLayout()
    self.lev1TreeEntry.setLayout(layout)
    layout.addWidget(QLabel(self.name))
    layout.addStretch(1)
    layout.addWidget(self.closeButton)
  
  def readLev2(self, hdf5File):  
    for lev2Group in lev1Group.keys(): # Level 2 loop 
      if isinstance(lev1Group[lev2Group], h5py.Group):
        self.groupsLev2Collector.append(lev2Container(self.tree, self, lev1Group[lev2Group]))
   
class lev2Container(QTreeWidgetItem):
  def __init__(self, tree, parent, lev2Group):
    super().__init__(parent)
    self.tree = tree
    self.fullPath = lev2Group.name
    self.name = self.fullPath.split('/')[-1]
    # Create Widgets and add entry in tree (at level 2) of GUI
    self.createLev2TreeEntry()
    self.tree.setItemWidget(self, 0, self.lev2TreeEntry)
    # Read available data sets
    self.dataSetsLev3Collector = []
    self.readDataSets(lev2Group)
      
  def createLev2TreeEntry(self):
    self.lev2TreeEntry = QWidget()
    layout = QHBoxLayout()
    self.lev2TreeEntry.setLayout(layout)
    layout.addWidget(QLabel(self.name.split('/')[-1])) 
    layout.addStretch(1)
  
  def readDataSets(self, lev2Group):  
    for DataSet in lev2Group.keys(): # Level 2 loop 
      if isinstance(lev2Group[DataSet], h5py.Dataset):
        self.dataSetsLev3Collector.append(lev3Container(self.tree, self, lev2Group[DataSet]))
    
class lev3Container(QTreeWidgetItem):
  def __init__(self, tree, parent, DataSet):
    super().__init__(parent)
    self.tree = tree
    self.fullPath = DataSet.name
    self.name = self.fullPath.split('/')[-1]
    # Create Widgets and add entry in tree (at level 3 / dataSet level) of GUI
    self.createDataSetTreeEntry(parent.name)
    self.tree.setItemWidget(self, 0, self.DataSetTreeEntry)
  
  def createDataSetTreeEntry(self, type):
    self.DataSetTreeEntry = QWidget()
    layout = QHBoxLayout()
    self.DataSetTreeEntry.setLayout(layout)
    self.drawButton = QPushButton('draw')
    self.drawButton.setFixedSize(15,15)
    self.drawButton.setToolTip('<b>draw</b>')
    layout.addWidget(QLabel(self.name))
    layout.addWidget(self.drawButton)
    # Select method according to type
    if type == 'Geometry':
      self.createDataSetTreeEntryInGeometry(layout)
    elif type == 'Setup':
      self.createDataSetTreeEntryInSetup(layout)
    elif type == 'Results':
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