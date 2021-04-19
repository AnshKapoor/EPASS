#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow, QLabel, QLineEdit
from standardWidgets import removeButton, editButton, setupWindow, messageboxOK, progressWindow
from materials import material

#########################################################

#########################################################
### Material Widget - Structural Isotropic            ###
#########################################################

class Structural_Isotropic(material):
    def __init__(self, Name, Id, E, nu, A, I, Ix, Iy, Iz, rho, t, Fi):
        #
        super(Structural_Isotropic, self).__init__()
        self.removeButton = removeButton()
        self.editButton = editButton()
        self.type = 'Structural_Isotropic'
        self.label = QLabel(self.type)
        #
        self.name = QLineEdit(Name)
        #self.name.setFixedWidth(75)
        self.Id = QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.E = QLineEdit(str(E))
        self.E.setToolTip("Youngs Modulus")
        self.E.setFixedWidth(100)
        self.nu = QLineEdit(str(nu))
        self.nu.setToolTip("Poissons ratio")
        self.nu.setFixedWidth(50)
        self.A = QLineEdit(str(A))
        self.A.setToolTip("Cross section(only for beam elements)")
        self.A.setFixedWidth(50)
        self.I = QLineEdit(str(I))
        self.I.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.I.setFixedWidth(50)
        self.Ix = QLineEdit(str(Ix))
        self.Ix.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.Ix.setFixedWidth(50)
        self.Iy = QLineEdit(str(Iy))
        self.Iy.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.Iy.setFixedWidth(50)
        self.Iz = QLineEdit(str(Iz))
        self.Iz.setToolTip("Moment of inertia(only for BeamBernoulli and BeamTimoshenko)")
        self.Iz.setFixedWidth(50)
        self.rho = QLineEdit(str(rho))
        self.rho.setToolTip("Density")
        self.rho.setFixedWidth(50)
        self.t = QLineEdit(str(t))
        self.t.setToolTip("Thickness")
        self.t.setFixedWidth(50)
        self.Fi = QLineEdit(str(Fi))
        self.Fi.setToolTip("Initial force to prestress element")
        self.Fi.setFixedWidth(50)
        self.length = 25
        self.type = QLabel('Isotropic:')
        self.type.setToolTip('<b>Type of Material</b> <br> Simple elastic material to be used with any structural element - without any damping.')
        #
        [self.addWidget(mat) for mat in [self.removeButton, self.Id, self.label, self.name, self.editButton]]
          
    # returns the material parameters and labels to the Parent class-exp_material    
    def getInfo(self):
        return [self.type, QLabel('Name'), self.name, QLabel('Id'), self.Id,
                QLabel('E'), self.E, QLabel('ν'), self.nu,
                QLabel('A'), self.A, QLabel('I'), self.I,
                QLabel('Ix'), self.Ix, QLabel('Iy'), self.Iy, QLabel('Iz'), self.Iz,
                QLabel('ρ'), self.rho, QLabel('t'), self.t, QLabel('Φ'), self.Fi,
                self.length]
    
    # returns data used for export to myMaterials.txt
    def getExportData(self):
        export_data = ['Isotropic', self.name.text(), self.Id.text(), self.E.text(), self.nu.text(), self.A.text(), self.I.text(), self.Ix.text(), self.Iy.text(), self.Iz.text(), self.rho.text(), self.t.text(), self.Fi.text()]
        export_data = [str(item) for item in export_data] # convert QtCore.QString elements to str
        return export_data
    
    # returns the material parameters and labels to the Parent class-exp_material    
    def getParaStudy(self):
        return ['E', 'nu', 'A', 'I', 'Ix', 'Iy', 'Iz', 'rho', 't', 'Fi']


