#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow, QLabel, QLineEdit
from standardWidgets import removeButton, editButton, messageboxOK, progressWindow
from materials import material

#########################################################

#########################################################
### Material Widget - Structural Isotropic            ###
#########################################################

class STR_LIN_ELA_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.type = 'STR_LIN_ELA_ISO_DIR'
        self.type.setToolTip('<b>Type of Material</b> <br> Simple elastic material to be used with any structural element - without any damping.')
        #
        self.parameterNames =                              ['E',  'nu', 'A', 'Ix', 'Iy', 'Iz', 'rho', 't', 'Fi']
        self.parameterValues = [QLineEdit(str(x)) for x in [7.e9,  0.3,  0.,   0.,   0.,   0., 2700.,  0.,   0.]]
        self.parameterTipps = ['Youngs Modulus', 'Poissons ratio', 'Cross section(only for beam elements)',  ... 
                               'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia(only for BeamBernoulli and BeamTimoshenko)', ...
                               'Density', 'Thickness', 'Initial force to prestress element']
        [parameterValue.setToolTip(self.parameterTipps[n]) for parameterValue, n in enumerate(self.parameterValues)]
        #
        super(Structural_Isotropic, self).__init__(Id)
        #
          
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


