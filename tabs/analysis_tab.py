import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow,QButtonGroup
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class analysis_tab(QtWidgets.QMainWindow):
    def __init__(self):
        super(analysis_tab, self).__init__()
        self.myFont = QFont("Verdana", 12)
        self.labelAna = QLabel('frequency range:')
        self.labelAna.setFont(self.myFont)
        self.freqEdit = QPushButton('...')
        self.freqEdit.setStyleSheet("background-color:rgb(255,255,255)")
        self.freqEdit.setStatusTip('Edit frequencies')
        self.freqEdit.setMaximumWidth(23)
        self.freqEdit.setMaximumHeight(23)
        self.freqstart = QLineEdit('100')
        self.startLabel = QLabel('Start [Hz]:')
        self.freqdelta = QLineEdit('10')
        self.deltaLabel = QLabel('Delta [Hz]:')
        self.freqsteps = QLineEdit('100')
        self.stepsLabel = QLabel('Steps:')
        self.freqEdit.clicked.connect(self.showSaveEdit)
        self.labelType = QLabel('Analysis Type:')
        self.selectorType = analysisTypeSelector()
        self.labelSolver = QLabel('Solver:')
        self.selectorSolver = solverTypeSelector()
        self.AnasepLine1 = sepLine()
        self.AnasepLine2 = sepLine()
        self.freqSaveButton = saveButton()
        self.freqSaveButton.clicked.connect(self.showSaveEdit)
        # ADD TO LAYOUT
        self.AnaLayout = QVBoxLayout()
        self.AnaLayout1 = QHBoxLayout()
        self.AnaLayout2 = QHBoxLayout()
        self.AnaLayout3 = QHBoxLayout()
        self.AnaLayout.addWidget(self.labelAna)
        self.AnaLayout1.addWidget(self.startLabel)
        self.AnaLayout1.addWidget(self.freqstart)
        self.AnaLayout1.addWidget(self.deltaLabel)
        self.AnaLayout1.addWidget(self.freqdelta)
        self.AnaLayout1.addWidget(self.stepsLabel)
        self.AnaLayout1.addWidget(self.freqsteps)
        self.AnaLayout1.addWidget(self.freqSaveButton)

        self.AnaLayout2.addWidget(self.labelType)
        self.AnaLayout2.addWidget(self.selectorType)
        self.AnaLayout2.addWidget(self.labelSolver)
        self.AnaLayout2.addWidget(self.selectorSolver)
        self.AnaLayout.addLayout(self.AnaLayout1, 2)
        self.AnaLayout.addWidget(self.AnasepLine1)
        self.AnaLayout.addLayout(self.AnaLayout2, 1)
        self.AnaLayout.addWidget(self.AnasepLine2)
        self.AnaLayout.addLayout(self.AnaLayout3, 1)
        self.basic()

    #basic appearence of the tab
    def basic(self):


        # Setting Layouts for all the widgets
        self.horiz_layout.addWidget(mat_label)
        self.horiz_layout.addWidget(self.comboBox)
        self.horiz_layout.addWidget(addMat)
        self.horiz_layout.addWidget(saveMat)
        self.main_layout.addLayout(self.horiz_layout,0,0,Qt.AlignTop)
        widget = QWidget()
        widget.setLayout(self.main_layout)
        self.setCentralWidget(widget)


        #self.show_mat() # to display materials added
        self.show()
