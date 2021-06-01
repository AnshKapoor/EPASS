# Modules
import os
import h5py
import numpy as np
from DataStructure import lev1Container
from PyQt5.QtWidgets import QFileDialog
#from PyQt5.QtCore import 
#from PyQt5.QtGui import

class Controller():
  def __init__(self, inaGui):
    self.inaGui = inaGui
    self.tree = self.inaGui.dataTree
    # Connectors 
    self.inaGui.loadAct.triggered.connect(self.loadFile)
    # List of loaded level 1 groups
    self.groupsLev1Collector = []
    # Dummycode which must be addressed by button later
    #self.loadHdf5('example.hdf5')
  
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
      self.connectButtons(self.groupsLev1Collector[-1])
      #for level1Group in hdf5File.keys(): # Level 1 loop 
      #  if isinstance(hdf5File[level1Group], h5py.Group):
      #    
      #    
    
  def connectButtons(self,currentLev1Container):
    currentLev1Container.closeButton.clicked.connect(self.removeLev1Entry)
    for currentLev2Container in currentLev1Container.groupsLev2Collector:
      for currentLev3Container in currentLev2Container.dataSetsLev3Collector:
        currentLev3Container.drawButton.clicked.connect(self.drawData)

  def removeLev1Entry(self):
    closeButtonWhichSentSignal = self.inaGui.sender()
    indexOfLev1EntryToBeRemoved = [x.closeButton for x in self.groupsLev1Collector].index(closeButtonWhichSentSignal)
    self.tree.takeTopLevelItem(indexOfLev1EntryToBeRemoved)
    self.groupsLev1Collector.pop(indexOfLev1EntryToBeRemoved)
    
  def drawData(self):
    drawButtonWhichSentSignal = self.inaGui.sender()
    for currentLev1Container in self.groupsLev1Collector:
      for currentLev2Container in currentLev1Container.groupsLev2Collector:
        indexOfLev3Entry = [x.drawButton for x in currentLev2Container.dataSetsLev3Collector].index(drawButtonWhichSentSignal)
        dataSet = currentLev2Container.dataSetsLev3Collector[indexOfLev3Entry]
        dataSet.loadRequestedDataToMemory()
        #
        dataSet.releaseData()
        