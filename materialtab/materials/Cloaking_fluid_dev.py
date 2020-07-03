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
### Material Widget - cloaking fluid                  ###
#########################################################

class Cloaking_fluid():
    
    def __init__(self, Name, Id, c, rho, t, R_i_cl, R_o_cl, CSx_cl, CSy_cl, CSz_cl):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.c = QtWidgets.QLineEdit(str(c))
        self.c.setToolTip("Speed of Sound")
        self.c.setFixedWidth(100)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.R_i_cl = QtWidgets.QLineEdit(str(R_i_cl))
        self.R_i_cl.setToolTip("inner radius of cloak")
        self.R_i_cl.setFixedWidth(50)
        self.R_o_cl = QtWidgets.QLineEdit(str(R_o_cl))
        self.R_o_cl.setToolTip("outer radius of cloak")
        self.R_o_cl.setFixedWidth(50)
        self.CSx_cl = QtWidgets.QLineEdit(str(CSx_cl))
        self.CSx_cl.setToolTip("x coordinate of center of sphere")
        self.CSx_cl.setFixedWidth(50)
        self.CSy_cl = QtWidgets.QLineEdit(str(CSy_cl))
        self.CSy_cl.setToolTip("y coordinate of center of sphere")
        self.CSy_cl.setFixedWidth(50)
        self.CSz_cl = QtWidgets.QLineEdit(str(CSz_cl))
        self.CSz_cl.setToolTip("z coordinate of center of sphere")
        self.CSz_cl.setFixedWidth(50)
        self.length = 19
        self.type = QtWidgets.QLabel('Cloaking:')
        self.type.setToolTip('<b>Type of Material</b> <br> Cloaking material guides waves in a special way.')
          
    #returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('cf'), self.c, QtWidgets.QLabel('rhof'), self.rho, QtWidgets.QLabel('t'), self.t, QtWidgets.QLabel('R_i_cl'), self.R_i_cl, QtWidgets.QLabel('R_o_cl'), self.R_o_cl, QtWidgets.QLabel('CSx_cl'), self.CSx_cl, QtWidgets.QLabel('CSy_cl'), self.CSy_cl, QtWidgets.QLabel('CSz_cl'), self.CSz_cl, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Cloaking', self.name.text(), self.Id.text(), self.c.text(), self.rho.text(), self.t.text(), self.R_i_cl.text(), self.R_o_cl.text(), self.CSx_cl.text(), self.CSy_cl.text(), self.CSz_cl.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['cf', 'rhof', 't', 'R_i_cl', 'R_o_cl', 'CSx_cl', 'CSy_cl', 'CSz_cl']