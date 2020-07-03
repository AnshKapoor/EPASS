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
### Material Widget - fluid including loss mechanisms ###
#########################################################

class equivfluid():
    QtWidgets
    def __init__(self, Name, Id, c, rho, t, creal, cimag, rhoreal, rhoimag):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.c = QtWidgets.QLineEdit(str(c))
        self.c.setToolTip("Speed of Sound in Fluid")
        self.c.setFixedWidth(100)
        self.rho = QtWidgets.QLineEdit(str(rho))
        self.rho.setToolTip("Density of the fluid")
        self.rho.setFixedWidth(50)
        self.t = QtWidgets.QLineEdit(str(t))
        self.t.setToolTip("Thickness of fluid domain (only for 2D fluid elements)")
        self.t.setFixedWidth(50)
        self.creal = QtWidgets.QLineEdit(str(creal))
        self.creal.setToolTip("Real part of complex speed of sound")
        self.creal.setFixedWidth(50)
        self.cimag = QtWidgets.QLineEdit(str(cimag))
        self.cimag.setToolTip("Imaginary part of complex speed of sound")
        self.cimag.setFixedWidth(50)
        self.rhoreal = QtWidgets.QLineEdit(str(rhoreal))
        self.rhoreal.setToolTip("Real part of complex density")
        self.rhoreal.setFixedWidth(50)
        self.rhoimag = QtWidgets.QLineEdit(str(rhoimag))
        self.rhoimag.setToolTip("Imaginary part of complex density")
        self.rhoimag.setFixedWidth(50)
        self.length = 19
        self.type = QtWidgets.QLabel('Fluidequivdirect:')
        self.type.setToolTip('<b>Type of Material</b> <br> Fluid material to be used with fluid elements - with damping.')
        
    #returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('cf'), self.c, QtWidgets.QLabel('rhof'), self.rho, QtWidgets.QLabel('t'), self.t, QtWidgets.QLabel('creal'), self.creal, QtWidgets.QLabel('cimag'), self.cimag, QtWidgets.QLabel('rhoreal'), self.rhoreal, QtWidgets.QLabel('rhoimag'), self.rhoimag, self.length]
        
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['EquivalentFluid2', self.name.text(), self.Id.text(), self.c.text(), self.rho.text(), self.t.text(), self.creal.text(), self.cimag.text(), self.rhoreal.text(), self.rhoimag.text()]    
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
            
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['cf', 'rhof', 't', 'creal', 'cimag', 'rhoreal', 'rhoimag']
        