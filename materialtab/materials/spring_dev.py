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

class spring():
    
    def __init__(self, Name, Id, Cx, Cy, Cz, Crx, Cry, Crz, typ, eta):

        self.name = QtWidgets.QLineEdit(Name)
        self.name.setFixedWidth(75)
        self.Id = QtWidgets.QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.Cx = QtWidgets.QLineEdit(str(Cx))
        self.Cx.setToolTip("translational stiffness in x")
        self.Cx.setFixedWidth(50)
        self.Cy = QtWidgets.QLineEdit(str(Cy))
        self.Cy.setToolTip("translational stiffness in y")
        self.Cy.setFixedWidth(50)
        self.Cz = QtWidgets.QLineEdit(str(Cz))
        self.Cz.setToolTip("translational stiffness in z")
        self.Cz.setFixedWidth(50)
        self.Crx = QtWidgets.QLineEdit(str(Crx))
        self.Crx.setToolTip("rotational stiffness in x")
        self.Crx.setFixedWidth(50)
        self.Cry = QtWidgets.QLineEdit(str(Cry))
        self.Cry.setToolTip("rotational stiffness in y")
        self.Cry.setFixedWidth(50)
        self.Crz = QtWidgets.QLineEdit(str(Crz))
        self.Crz.setToolTip("rotational stiffness in z")
        self.Crz.setFixedWidth(50)
        self.typ = QtWidgets.QLineEdit(str(typ))
        self.typ.setToolTip("type of viscoelastic behaviour (1 or 2)")
        self.typ.setFixedWidth(50)
        self.eta = QtWidgets.QLineEdit(str(eta))
        self.eta.setToolTip("loss factor")
        self.eta.setFixedWidth(50)
        self.length = 21
        self.type = QtWidgets.QLabel('Spring:')
        self.type.setToolTip('<b>Type of Material</b> <br> Spring Material can only be used with spring elements to provide information on discrete stiffness for each degree of freedom. If elastic (real) spring should be used, loss factor is zero.')
          
    # returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QtWidgets.QLabel('Name'), self.name, QtWidgets.QLabel('Id'), self.Id, QtWidgets.QLabel('Cx'), self.Cx, QtWidgets.QLabel('Cy'), self.Cy, QtWidgets.QLabel('Cz'), self.Cz, QtWidgets.QLabel('Crx'), self.Crx, QtWidgets.QLabel('Cry'), self.Cry, QtWidgets.QLabel('Crz'), self.Crz, QtWidgets.QLabel('typ'), self.typ, QtWidgets.QLabel('eta'), self.eta, self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Spring', self.name.text(), self.Id.text(), self.Cx.text(), self.Cy.text(), self.Cz.text(), self.Crx.text(), self.Cry.text(), self.Crz.text(), self.typ.text(), self.eta.text()]    
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['Cx', 'Cy', 'Cz', 'Crx', 'Cry', 'Crz', 'typ', 'eta']
 