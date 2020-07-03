#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
#########################################################
import sys
import os
from PyQt5 import QtGui,QtCore,QtWidgets
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow

#########################################################
### Material Widget - Structural Isotropic            ###
#########################################################

class pointmass():
    
    def __init__(self, Name, Id, m):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.m = QtWidgets.QLineEdit(str(m))
        self.m.setToolTip("mass")
        self.m.setFixedWidth(50)
        self.length = 7
        self.type = QtWidgets.QLabel('Pointmass:')
        self.type.setToolTip('<b>Type of Material</b> <br>Material for definition of mass for pointmass.')
          
    # returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('M'), self.m, self.length]
        
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Pointmass', self.name.text(), self.Id.text(), self.m.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
        
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['M']
 