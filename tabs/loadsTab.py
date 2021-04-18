import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow,QButtonGroup
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from standardWidgets import *
from loads import loadInfoBox

from planeWave import planeWave
from diffuseField import diffuseField
from timeVarDat import timeVarDat
from tbl import tbl

class loadsTab(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.tabLayout = QVBoxLayout(self)
        self.subLayouts = []
        self.changeObjects = []
        self.myFont = QFont("Verdana", 12)
        self.titleText = "Loads"
        #
        self.typeLabel = QLabel('Load Type')
        self.loadSelector = loadTypeSelector()
        self.addLoadButton = addButton()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.typeLabel)
        self.subLayouts[-1].addWidget(self.loadSelector)
        self.subLayouts[-1].addWidget(self.addLoadButton)
        self.subLayouts[-1].addStretch()
        #
        self.loadInfo = loadInfoBox()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].setStretchFactor(self.loadInfo, True)
        self.subLayouts[-1].addWidget(self.loadInfo)
        #
        [self.tabLayout.addLayout(layout) for layout in self.subLayouts]
        
    def addLoad(self, myModel):
        """
        Add the load selected by self.loadSelector (self.addLoadButton click event)
        """
        if myModel.hdf5File:
            if self.loadSelector.currentText() == 'Plane wave':
                myModel.loads.append(planeWave(myModel))
            # if self.loadSelector.currentText() == 'Diffuse field':
                # myModel.loads.append(diffuseField(myModel))
            # if self.loadSelector.currentText() == 'Distributed time domain load':
                # myModel.loads.append(timeVarDat(myModel))
            # if self.loadSelector.currentText() == 'Turbulent Boundary Layer':
                # myModel.loads.append(tbl(myModel))
            # Refresh layout
            self.loadInfo.clearLayout()
            self.loadInfo.updateLayout(myModel.loads)
            return 1
        else:
            messageboxOK('Addition of load not possible', 'Open a model first!')
            return 0
    
    def removeLoad(self, loadIDToRemove, myModel):
        """
        Remove a load from list (removeButton click event)
        """
        # Layout is cleared
        self.loadInfo.clearLayout()
        if loadIDToRemove=='button':
            loadIDToRemove = self.sender().id
        myModel.loads[loadIDToRemove].drawCheck.setChecked(0)
        myModel.loads[loadIDToRemove].clearLayout() # Set widgets to None (remove Button etc)
        myModel.loads[loadIDToRemove] = None # Set the pointer to None
        myModel.loads.pop(loadIDToRemove) # Remove the entry in list
        self.loadInfo.updateLayout(myModel.loads)
    
    def update(self, myModel):
        pass
    
    def data2hdf5(self, myModel): 
        try:
            # Write possibly changed values to hdf5 file
            #g = myModel.hdf5File['Analysis']
            # g.attrs['id'] = myModel.analysisID 
            return 1
        except:
            return 0
    