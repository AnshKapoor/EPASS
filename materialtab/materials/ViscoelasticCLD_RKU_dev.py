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

class ViscoelasticCLD_RKU():
    
    def __init__(self, Name, Id, E1, eta1, nu1, G2, eta2, nu2, E3, eta3, nu3, rho1, rho2, rho3, H1, H2, H3, Btyp):

        self.type = QtWidgets.QLabel('Visco_cld_rku:')
        self.type.setToolTip('<b>Type of Material</b> <br> Cremer/Heckl simple constrained layer damping (CLD) model intended to be used with shell elements only.')
        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)        
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        
        self.E1 = QtWidgets.QLineEdit(str(E1))
        self.E1.setToolTip("Youngs Modulus of base plate (layer 1)")
        self.E1.setFixedWidth(100)        
        self.eta1 = QtWidgets.QLineEdit(str(eta1))
        self.eta1.setToolTip("Lossfactor of base plate (layer 1)")
        self.eta1.setFixedWidth(50)
        self.nu1 = QtWidgets.QLineEdit(str(nu1))
        self.nu1.setToolTip("Poisson's ratio of base plate (layer 1)")
        self.nu1.setFixedWidth(50)
        self.rho1 = QtWidgets.QLineEdit(str(rho1))
        self.rho1.setToolTip("Density of base plate (layer 1)")
        self.rho1.setFixedWidth(50)
        self.H1 = QtWidgets.QLineEdit(str(H1))
        self.H1.setToolTip("Thickness of base plate (layer 1)")
        self.H1.setFixedWidth(50)
        
        self.G2 = QtWidgets.QLineEdit(str(G2))
        self.G2.setToolTip("Shear modulus of viscoelastic middle layer (layer 2)")
        self.G2.setFixedWidth(100)
        self.eta2 = QtWidgets.QLineEdit(str(eta2))
        self.eta2.setToolTip("Lossfactor of viscoelastic middle layer (layer 2)")
        self.eta2.setFixedWidth(50)
        self.nu2 = QtWidgets.QLineEdit(str(nu2))
        self.nu2.setToolTip("Poisson's ratio of viscoelastic middle layer (layer 2)")
        self.nu2.setFixedWidth(50)
        self.rho2 = QtWidgets.QLineEdit(str(rho2))
        self.rho2.setToolTip("Density of viscoelastic middle layer (layer 2)")
        self.rho2.setFixedWidth(50)
        self.H2 = QtWidgets.QLineEdit(str(H2))
        self.H2.setToolTip("Thickness of viscoelastic middle layer (layer 2)")
        self.H2.setFixedWidth(50)
        
        self.E3 = QtWidgets.QLineEdit(str(E3))
        self.E3.setToolTip("Youngs Modulus of constraining covering layer (layer 3)")
        self.E3.setFixedWidth(100)
        self.eta3 = QtWidgets.QLineEdit(str(eta3))
        self.eta3.setToolTip("Lossfactor of constraining covering layer (layer 3)")
        self.eta3.setFixedWidth(50)
        self.nu3 = QtWidgets.QLineEdit(str(nu3))
        self.nu3.setToolTip("Poisson's ratio of constraining covering layer (layer 3)")
        self.nu3.setFixedWidth(50)
        self.rho3 = QtWidgets.QLineEdit(str(rho3))
        self.rho3.setToolTip("Density of constraining covering layer (layer 3)")
        self.rho3.setFixedWidth(50)
        self.H3 = QtWidgets.QLineEdit(str(H3))
        self.H3.setToolTip("Thickness of constraining covering layer (layer 3)")
        self.H3.setFixedWidth(50)
        
        self.Btyp = QtWidgets.QLineEdit(str(Btyp))
        self.Btyp.setToolTip("Type of bending stiffness used for the base plate: 0 - RKU bending stiffness, 1 - Laminate theory bending stiffness")
        self.Btyp.setFixedWidth(50)
        
        self.length = 35
        
    #returns the material parameters and labels to the Parent class-exp_material
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id,
                QtWidgets.QLabel('E1'), self.E1, QtWidgets.QLabel('eta1'), self.eta1, QtWidgets.QLabel('nu1'), self.nu1,
                QtWidgets.QLabel('G2'), self.G2, QtWidgets.QLabel('eta2'), self.eta2, QtWidgets.QLabel('nu2'), self.nu2,
                QtWidgets.QLabel('E3'), self.E3, QtWidgets.QLabel('eta3'), self.eta3, QtWidgets.QLabel('nu3'), self.nu3,
                QtWidgets.QLabel('rho1'), self.rho1, QtWidgets.QLabel('rho2'), self.rho2, QtWidgets.QLabel('rho3'), self.rho3,
                QtWidgets.QLabel('H1'), self.H1, QtWidgets.QLabel('H2'), self.H2, QtWidgets.QLabel('H3'), self.H3,
                QtWidgets.QLabel('Btyp'), self.Btyp,
                self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['CLD:Ross/Kerwin/Ungar', self.name.text(), self.Id.text(),
                       self.E1.text(), self.eta1.text(), self.nu1.text(),
                       self.G2.text(), self.eta2.text(), self.nu2.text(),
                       self.E3.text(), self.eta3.text(), self.nu3.text(),
                       self.rho1.text(), self.rho2.text(), self.rho3.text(),
                       self.H1.text(), self.H2.text(), self.H3.text(),
                       self.Btyp.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material
    def getParaStudy(self):
        return ['E1', 'eta1', 'nu1', 'G2', 'eta2', 'nu2', 'E3', 'eta3', 'nu3', 'rho1', 'rho2', 'rho3', 'H1', 'H2', 'H3', 'Btyp']
        