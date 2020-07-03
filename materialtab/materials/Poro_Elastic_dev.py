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
### Material Widget - 3D poro-elastic material        ###
#########################################################

class Poro_Elastic():
    
    def __init__(self, Name, Id, E, eta, nu, rho, rhof, alinf, R, phi, lamda, lamdat):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.E = QtWidgets.QLineEdit(str(E))
        self.E.setToolTip("Youngs Modulus")
        self.E.setFixedWidth(100)
        self.eta = QtWidgets.QLineEdit(str(eta))
        self.eta.setToolTip("Damping coefficient")
        self.eta.setFixedWidth(50)
        self.nu = QtWidgets.QLineEdit(str(nu))
        self.nu.setToolTip("Poissons ratio")
        self.nu.setFixedWidth(50)
        self.rho =QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density of structure material")
        self.rho.setFixedWidth(50)
        self.rhof = QtWidgets.QLineEdit(str(rhof))
        self.rhof.setToolTip("Density of pore fluid")
        self.rhof.setFixedWidth(50)
        self.alinf = QtWidgets.QLineEdit(str(alinf))
        self.alinf.setToolTip("Tortuosity")
        self.alinf.setFixedWidth(50)
        self.R = QtWidgets.QLineEdit(str(R))
        self.R.setToolTip("Flow resistivity")
        self.R.setFixedWidth(50)
        self.phi = QtWidgets.QLineEdit(str(phi))
        self.phi.setToolTip("Porosity")
        self.phi.setFixedWidth(50)
        self.lamda = QtWidgets.QLineEdit(str(lamda))
        self.lamda.setToolTip("Characteristic thermal length")
        self.lamdat = QtWidgets.QLineEdit(str(lamdat))
        self.lamdat.setToolTip("Characteristic viscous length")
        self.lamdat.setFixedWidth(25)
        self.length = 24
        self.type = QtWidgets.QLabel('Poro3d:')
        self.type.setToolTip('<b>Type of Material</b> <br> 3D Biot model for poro-elastic element types.')
          
    #returns the material parameters and labels to the Parent class-exp_material            
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('E'), self.E, QtWidgets.QLabel('eta'), self.eta, QtWidgets.QLabel('nu'), self.nu, QtWidgets.QLabel('rho'), self.rho, QtWidgets.QLabel('rhof'), self.rhof, QtWidgets.QLabel('alinf'), self.alinf, QtWidgets.QLabel('R'), self.R, QtWidgets.QLabel('phi'), self.phi, QtWidgets.QLabel('lamda'), self.lamda, QtWidgets.QLabel('lamdat'), self.lamdat, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Poro3d', self.name.text(), self.Id.text(), self.E.text(), self.eta.text(), self.nu.text(), self.rho.text(), self.rhof.text(), self.alinf.text(), self.R.text(), self.phi.text(), self.lamda.text(), self.lamdat.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
        
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['E', 'eta', 'nu', 'rho', 'rhof', 'alinf', 'R', 'phi', 'lamda', 'lamdat']
