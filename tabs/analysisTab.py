import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow,QButtonGroup
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from standardWidgets import *
import numpy as np

class analysisTab(QWidget):
    def __init__(self, parent = None):
        #super(analysisTab, self).__init__()
        QWidget.__init__(self, parent)
        self.tabLayout = QVBoxLayout(self)
        self.subLayouts = []
        self.changeObjects = []
        self.myFont = QFont("Verdana", 12)
        self.titleText = "Analysis"
        #
        self.typeLabel = QLabel('Analysis Type')
        self.typeSelector = analysisTypeSelector()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.typeLabel)
        self.subLayouts[-1].addWidget(self.typeSelector)
        #
        self.solverLabel = QLabel('Solver')
        self.solverSelector = solverTypeSelector()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.solverLabel)
        self.subLayouts[-1].addWidget(self.solverSelector)
        #
        self.subLayouts.append(QVBoxLayout())
        self.subLayouts[-1].addWidget(sepLine())
        #
        self.freqLabel = QLabel('Frequency range')
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.freqLabel)
        #
        self.startLabel = QLabel('Start [Hz]:')
        self.freqStart = QLineEdit()
        self.changeObjects.append(self.freqStart)
        self.stepsLabel = QLabel('Steps:')
        self.freqSteps = QLineEdit()
        self.changeObjects.append(self.freqSteps)
        self.deltaLabel = QLabel('Delta [Hz]:')
        self.freqDelta = QLineEdit()
        self.changeObjects.append(self.freqDelta)
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.startLabel)
        self.subLayouts[-1].addWidget(self.freqStart)
        self.subLayouts[-1].addWidget(self.stepsLabel)
        self.subLayouts[-1].addWidget(self.freqSteps)
        self.subLayouts[-1].addWidget(self.deltaLabel)
        self.subLayouts[-1].addWidget(self.freqDelta)
        #
        self.descriptionLabel = QLabel('Description:')
        self.description = QLineEdit()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.descriptionLabel)
        self.subLayouts[-1].addWidget(self.description)
        #
        self.subLayouts.append(QVBoxLayout())
        self.subLayouts[-1].addWidget(sepLine())
        #
        [self.tabLayout.addLayout(layout) for layout in self.subLayouts]
        self.tabLayout.addStretch()
        
    def update(self, myModel):
        self.typeSelector.changeTo(myModel.analysisType)
        self.solverSelector.changeTo(myModel.solverType)
        self.freqStart.setText(str(myModel.freqStart))
        self.freqSteps.setText(str(myModel.freqSteps))
        self.freqDelta.setText(str(myModel.freqDelta))
        self.description.setText(str(myModel.description))
    
    def data2hdf5(self, myModel): 
        try:
            # Write possibly changed values to hdf5 file
            g = myModel.hdf5File['Analysis']
            # g.attrs['id'] = myModel.analysisID 
            # g.attrs['type'] = myModel.analysisType 
            g.attrs['start'] = np.float64(self.freqStart.text())
            g.attrs['steps'] = np.uint64(self.freqSteps.text())
            g.attrs['delta'] = np.float64(self.freqDelta.text())
            # g.attrs['solver'] = myModel.solverType
            # g.attrs['revision'] = myModel.revision
            g.attrs['description'] = self.description.text()
            return 1
        except:
            return 0
    