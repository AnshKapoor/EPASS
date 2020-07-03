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
### Material Widget - fluid                           ###
#########################################################

class Fluid():
    
    def __init__(self, Name, Id, c, rho, t):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.c = QtWidgets.QLineEdit(str(c))
        self.c.setToolTip("Speed of Sound")
        self.c.setFixedWidth(100)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density of fluid")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.length = 11
        self.type = QtWidgets.QLabel('Fluid:')
        self.type.setToolTip('<b>Type of Material</b> <br> Simple fluid material to be used with fluid elements - without any damping.')
          
    #returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('cf'), self.c, QtWidgets.QLabel('rhof'), self.rho, QtWidgets.QLabel('t'), self.t, self.length]
        
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Fluid', self.name.text(), self.Id.text(), self.c.text(), self.rho.text(), self.t.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
        
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['cf', 'rhof', 't']
        