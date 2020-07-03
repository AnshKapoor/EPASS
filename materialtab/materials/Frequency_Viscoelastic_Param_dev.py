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

class Frequency_Viscoelastic_Param():
    
    def __init__(self, Name, Id, E0, E1, E2, Eta0, alpha, beta, nu, A, Ix, Iy, Iz, rho, t):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.E0 = QtWidgets.QLineEdit(str(E0))
        self.E0.setToolTip("Static Young's modulus for parametric model")
        self.E0.setFixedWidth(100)
        self.E1 = QtWidgets.QLineEdit(str(E1))
        self.E1.setToolTip("E1 factor for parametric model")
        self.E1.setFixedWidth(100)
        self.E2 = QtWidgets.QLineEdit(str(E2))
        self.E2.setToolTip("E2 factor for parametric model")
        self.E2.setFixedWidth(100)
        self.Eta0 = QtWidgets.QLineEdit(str(Eta0))
        self.Eta0.setToolTip("Basic loss factor for parametric model")
        self.Eta0.setFixedWidth(50)
        self.alpha = QtWidgets.QLineEdit(str(alpha))
        self.alpha.setToolTip("alpha factor for parametric model")
        self.alpha.setFixedWidth(50)
        self.beta = QtWidgets.QLineEdit(str(beta))
        self.beta.setToolTip("beta factor for parametric model")
        self.beta.setFixedWidth(50)
        self.nu = QtWidgets.QLineEdit(str(nu))
        self.nu.setToolTip("Poissons ratio")
        self.nu.setFixedWidth(50)
        self.A = QtWidgets.QLineEdit(str(A))
        self.A.setToolTip("Cross section area")
        self.A.setFixedWidth(50)
        self.Ix = QtWidgets.QLineEdit(str(Ix))
        self.Ix.setToolTip("Moment of inertia in x")
        self.Ix.setFixedWidth(50)
        self.Iy = QtWidgets.QLineEdit(str(Iy))
        self.Iy.setToolTip("Moment of inertia in y")
        self.Iy.setFixedWidth(50)
        self.Iz = QtWidgets.QLineEdit(str(Iz))
        self.Iz.setToolTip("Moment of inertia in z")
        self.Iz.setFixedWidth(50)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.length = 31
        self.type = QtWidgets.QLabel('Viscofreqparam:')
        self.type.setToolTip('<b>Type of Material</b> <br> Visco-elastic parametric material with frequency-dependent e-modulus and eta according to E(omega)=E0+E1*omega+E2*omega*omega and eta(omega)=Eta0+alpha/omega+beta*omega. To be used with any structural element.')
          
    #returns the material parameters and labels to the Parent class-exp_material            
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('E0'), self.E0,QtWidgets.QLabel('E1'), self.E1, QtWidgets.QLabel('E2'), self.E2, QtWidgets.QLabel('Eta0'), self.Eta0, QtWidgets.QLabel('alpha'), self.alpha, QtWidgets.QLabel('beta'), self.beta, QtWidgets.QLabel('nu'), self.nu, QtWidgets.QLabel('A'), self.A, QtWidgets.QLabel('Ix'), self.Ix, QtWidgets.QLabel('Iy'), self.Iy, QtWidgets.QLabel('Iz'), self.Iz, QtWidgets.QLabel('rho'), self.rho, QtWidgets.QLabel('t'), self.t, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Viscofreqparam', self.name.text(), self.Id.text(), self.E0.text(), self.E1.text(), self.E2.text(), self.Eta0.text(), self.alpha.text(), self.beta.text(), self.nu.text(), self.A.text(), self.Ix.text(), self.Iy.text(), self.Iz.text(), self.rho.text(), self.t.text()]    
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
     
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['E0', 'E1', 'E2', 'Eta0', 'alpha', 'beta', 'nu', 'A', 'Ix', 'Iy', 'Iz', 'rho', 't']   
        