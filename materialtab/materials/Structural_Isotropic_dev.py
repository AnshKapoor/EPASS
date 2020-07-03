#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
import sys
import os
from PyQt5 import QtGui,QtCore,QtWidgets
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow


#########################################################

#########################################################
### Material Widget - Structural Isotropic            ###
#########################################################

class Structural_Isotropic():
    
    def __init__(self, Name, Id, E, nu, A, I, Ix, Iy, Iz, rho, t, Fi):


        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.E = QtWidgets.QLineEdit(str(E))
        self.E.setToolTip("Youngs Modulus")
        self.E.setFixedWidth(100)
        self.nu = QtWidgets.QLineEdit(str(nu))
        self.nu.setToolTip("Poissons ratio")
        self.nu.setFixedWidth(50)
        self.A = QtWidgets.QLineEdit(str(A))
        self.A.setToolTip("Cross section(only for beam elements)")
        self.A.setFixedWidth(50)
        self.I = QtWidgets.QLineEdit(str(I))
        self.I.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.I.setFixedWidth(50)
        self.Ix = QtWidgets.QLineEdit(str(Ix))
        self.Ix.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.Ix.setFixedWidth(50)
        self.Iy = QtWidgets.QLineEdit(str(Iy))
        self.Iy.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.Iy.setFixedWidth(50)
        self.Iz = QtWidgets.QLineEdit(str(Iz))
        self.Iz.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.Iz.setFixedWidth(50)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.Fi = QtWidgets.QLineEdit(str(Fi))
        self.Fi.setToolTip("Initial force to prestress element")
        self.Fi.setFixedWidth(50)
        self.length = 25
        self.type = QtWidgets.QLabel('Isotropic:')
        self.type.setToolTip('<b>Type of Material</b> <br> Simple elastic material to be used with any structural element - without any damping.')
          
    # returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type,QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id,
                QtWidgets.QLabel('E'), self.E, QtWidgets.QLabel('ν'), self.nu,
                QtWidgets.QLabel('A'), self.A, QtWidgets.QLabel('I'), self.I,
                QtWidgets.QLabel('Ix'), self.Ix, QtWidgets.QLabel('Iy'), self.Iy, QtWidgets.QLabel('Iz'), self.Iz,
                QtWidgets.QLabel('ρ'), self.rho, QtWidgets.QLabel('t'), self.t, QtWidgets.QLabel('Φ'), self.Fi,
                self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Isotropic', self.name.text(), self.Id.text(), self.E.text(), self.nu.text(), self.A.text(), self.I.text(), self.Ix.text(), self.Iy.text(), self.Iz.text(), self.rho.text(), self.t.text(), self.Fi.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['E', 'nu', 'A', 'I', 'Ix', 'Iy', 'Iz', 'rho', 't', 'Fi']


