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
### Material Widget - Visco-elastic material          ###
#########################################################

class Viscoelastic():
    
    def __init__(self, Name, Id, E, typ, eta, nu, A, I, rho, t):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.E = QtWidgets.QLineEdit(str(E))
        self.E.setToolTip("Youngs Modulus")
        self.E.setFixedWidth(100)
        self.typ = QtWidgets.QLineEdit(str(typ))
        self.typ.setToolTip("Damping Type")
        self.typ.setFixedWidth(50)
        self.eta = QtWidgets.QLineEdit(str(eta))
        self.eta.setToolTip("Lossfactor")
        self.eta.setFixedWidth(50)
        self.nu = QtWidgets.QLineEdit(str(nu))
        self.nu.setToolTip("Poissons ratio")
        self.nu.setFixedWidth(50)
        self.A = QtWidgets.QLineEdit(str(A))
        self.A.setToolTip("Cross section area")
        self.A.setFixedWidth(50)
        self.I = QtWidgets.QLineEdit(str(I))
        self.I.setToolTip("Moment of inertia")
        self.I.setFixedWidth(50)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.length = 21
        self.type = QtWidgets.QLabel('Visco:')
        self.type.setToolTip('<b>Type of Material</b> <br> Visco-elastic material with constant loss factor to calculate complex e-modulus.')
          
    #returns the material parameters and labels to the Parent class-exp_material        
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('E'), self.E, QtWidgets.QLabel('typ'), self.typ, QtWidgets.QLabel('eta'), self.eta, QtWidgets.QLabel('nu'), self.nu, QtWidgets.QLabel('A'), self.A, QtWidgets.QLabel('I'), self.I, QtWidgets.QLabel('rho'), self.rho, QtWidgets.QLabel('t'), self.t, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Viscoelastic', self.name.text(), self.Id.text(), self.E.text(), self.typ.text(), self.eta.text(), self.nu.text(), self.A.text(), self.I.text(), self.rho.text(), self.t.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['E', 'typ', 'eta', 'nu', 'A', 'I', 'rho', 't']
        