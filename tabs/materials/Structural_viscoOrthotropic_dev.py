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

class Structural_viscoOrthotropic():
    
    def __init__(self, Name, Id, Ex, Ey, Ez, eta, Gxy, Gxz, Gyz, nuxy, nuxz, nuyz, rho, t):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.Ex = QtWidgets.QLineEdit(str(Ex))
        self.Ex.setToolTip("Youngs Modulus in x direction")
        self.Ex.setFixedWidth(50)
        self.Ey = QtWidgets.QLineEdit(str(Ey))
        self.Ey.setToolTip("Youngs Modulus in y direction")
        self.Ey.setFixedWidth(50)
        self.Ez = QtWidgets.QLineEdit(str(Ez))
        self.Ez.setToolTip("Youngs Modulus in z direction")
        self.Ez.setFixedWidth(50)
        self.eta = QtWidgets.QLineEdit(str(eta))
        self.eta.setToolTip("Loss factor")
        self.eta.setFixedWidth(50)
        self.Gxy = QtWidgets.QLineEdit(str(Gxy))
        self.Gxy.setToolTip("Shear Modulus xy")
        self.Gxy.setFixedWidth(50)
        self.Gxz = QtWidgets.QLineEdit(str(Gxz))
        self.Gxz.setToolTip("Shear Modulus xz")
        self.Gxz.setFixedWidth(50)
        self.Gyz = QtWidgets.QLineEdit(str(Gyz))
        self.Gyz.setToolTip("Shear Modulus yz")
        self.Gyz.setFixedWidth(50)
        self.nuxy = QtWidgets.QLineEdit(str(nuxy))
        self.nuxy.setToolTip("Poissons ratio xy")
        self.nuxy.setFixedWidth(50)
        self.nuxz = QtWidgets.QLineEdit(str(nuxz))
        self.nuxz.setToolTip("Poissons ratio xz")
        self.nuxz.setFixedWidth(50)
        self.nuyz = QtWidgets.QLineEdit(str(nuyz))
        self.nuyz.setToolTip("Poissons ratio yz")
        self.nuyz.setFixedWidth(50)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.length = 29
        self.type = QtWidgets.QLabel('Viscoorthotropic:')
        self.type.setToolTip('<b>Type of Material</b> <br> Orthotropic linear visco-elastic material to be used with any structural element.')
          
    # returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('Ex'), self.Ex, QtWidgets.QLabel('Ey'), self.Ey, QtWidgets.QLabel('Ez'), self.Ez, QtWidgets.QLabel('eta'), self.eta, QtWidgets.QLabel('Gxy'), self.Gxy, QtWidgets.QLabel('Gxz'), self.Gxz, QtWidgets.QLabel('Gyz'), self.Gyz, QtWidgets.QLabel('nuxy'), self.nuxy, QtWidgets.QLabel('nuxz'), self.nuxz, QtWidgets.QLabel('nuyz'), self.nuyz, QtWidgets.QLabel(' ρ'), self.rho, QtWidgets.QLabel('t'), self.t, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Viscoorthotropic', self.name.text(), self.Id.text(), self.Ex.text(), self.Ey.text(), self.Ez.text(), self.eta.text(), self.Gxy.text(), self.Gxz.text(), self.Gyz.text(), self.nuxy.text(), self.nuxz.text(), self.nuyz.text(), self.rho.text(), self.t.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
        
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['Ex', 'Ey', 'Ez','eta', 'Gxy', 'Gxz', 'Gyz', 'nuxy', 'nuxz', 'nuyz','rho', 't']    
        
 