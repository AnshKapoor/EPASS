#
from PyQt5.QtWidgets import QApplication, QPushButton, QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy, QLabel, QLineEdit
import os
import numpy as np
import math
import h5py
from standardWidgets import progressWindow, removeButton, editButton, setupMaterialWindow

# ScrollArea containing loads in bottom left part of program
class matInfoBox(QScrollArea):
    def __init__(self):
        super(matInfoBox, self).__init__()
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Container widget for scroll area
        self.contWidget = QWidget()
        self.setWidget(self.contWidget)
        self.contLayout = QVBoxLayout(self.contWidget)

    # Clear all content in ScrollArea containing load info
    def clearLayout(self):
        ### Delete all layout content, if existing
        for i in reversed(range(self.contLayout.count())):
            if isinstance(self.contLayout.itemAt(i), QWidgetItem):
                self.contLayout.takeAt(i).widget().setParent(None)
            else:
                self.contLayout.removeItem(self.contLayout.takeAt(i))

    # Renew load content in ScrollArea
    def updateLayout(self, materials):
        self.clearLayout()
        [self.contLayout.addLayout(mat) for mat in materials]
        self.contLayout.addStretch(1)
        self.update()

# General material class
class material(QHBoxLayout):
    def __init__(self, Id):
        super(material, self).__init__()
        #
        self.removeButton = removeButton()
        self.Id = QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.label = QLabel(self.type)
        self.label.setToolTip(self.toolTip)
        self.name = QLineEdit('name')
        self.editButton = editButton()
        self.editButton.clicked.connect(self.showEdit)
        #
        self.initLayout()
        self.initSetupWindow()
    
    def initLayout(self): 
        [self.addWidget(wid) for wid in [self.removeButton, self.Id, self.label, self.name, self.editButton]]
    
    def clearLayout(self):
        """
        Clear all content in material layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))
    
    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupMaterialWindow('Material setup')
        # ADD TO LAYOUT
        [self.setupWindow.layout.addRow(QLabel(self.parameterNames[n]), self.parameterValues[n]) for n in range(len(self.parameterNames))]
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())
        
    def showEdit(self):
        """
        allows user to set parameters
        """
        self.varSave = [x.text() for x in self.parameterValues]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        return var
        
    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate(self.parameterValues):
            item.setText(self.varSave[n])    
    
    # def data2hdf5(self, elemLoadsGroup):
        # # Exporting the load per element
        # progWin = progressWindow(len(self.surfaceElements)-1, 'Exporting ' + self.type + ' load ' + str(self.removeButton.id+1))
        # for nE, surfaceElem in enumerate(self.surfaceElements):
            # frequencies = self.myModel.frequencies
            # dataArray = [[frequencies[nf], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][0], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][1], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][2], self.surfacePhases[nf,nE]] for nf in range(len(frequencies))]
            # set = elemLoadsGroup.create_dataset('/ElemLoads/mtxFemElemLoad'+str(self.removeButton.id+1) + '_' + str(int(surfaceElem)), data=(dataArray))
            # set.attrs['FreqCount'] = len(frequencies)
            # set.attrs['Id'] = str(self.removeButton.id+1) + str(surfaceElem)
            # set.attrs['ElementId'] = str(surfaceElem) # Assign element load to element
            # set.attrs['LoadType'] = self.type
            # set.attrs['MethodType'] = 'FEM'
            # # Update progress window
            # progWin.setValue(nE)
            # QApplication.processEvents()
        