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


####################################################################
### Material Widget - Frequency dependent visco-elastic material ###
####################################################################

class Frequency_Viscoelastic():
    
    def __init__(self, Name, Id, E, nu, rho, A, I, t):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.E = QtWidgets.QLineEdit(str(E))
        self.E.setToolTip("Youngs Modulus - filename")
        self.E.setFixedWidth(100)
        self.nu = QtWidgets.QLineEdit(str(nu))
        self.nu.setToolTip("Poissons ratio")
        self.nu.setFixedWidth(50)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.A = QtWidgets.QLineEdit(str(A))
        self.A.setToolTip("Cross section area")
        self.A.setFixedWidth(50)
        self.I = QtWidgets.QLineEdit(str(I))
        self.I.setToolTip("Moment of inertia")
        self.I.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.length = 17
        self.type = QtWidgets.QLabel('Viscofreq:')
        self.type.setToolTip('<b>Type of Material</b> <br> Visco-elastic material with frequency-dependend e-modulus which must be given in a file. To be used with any structural element.')
          
    #returns the material parameters and labels to the Parent class-exp_material            
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('E'), self.E, QtWidgets.QLabel('nu'), self.nu, QtWidgets.QLabel('rho'), self.rho, QtWidgets.QLabel('A'), self.A, QtWidgets.QLabel('I'), self.I, QtWidgets.QLabel('t'), self.t, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Viscofreq', self.name.text(), self.Id.text(), self.E.text(), self.nu.text(), self.rho.text(), self.A.text(), self.I.text(), self.t.text()]    
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['E', 'nu', 'rho', 'A', 'I', 't']   
        