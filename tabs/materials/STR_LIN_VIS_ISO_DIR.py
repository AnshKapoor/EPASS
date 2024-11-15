#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_VIS_ISO_DIR           ###
#########################################################

class STR_LIN_VIS_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear visco iso'
        self.type = 'STR_LIN_VIS_ISO_DIR'
        self.toolTip = '<b>Structural linear visco-elastic isotropic</b> <br>Material model according to Hookes law with damping loss factor.'
        #
        self.parameterNames =                              ['E' , 'type', 'eta', 'nu',  'A',  'Ix',  'Iy',  'Iz', 'rho', 't']
        self.parameterValues = [QLineEdit(str(x)) for x in [7.e10, 1     , 0.001, 0.3 ,   0.,    0.,    0.,    0., 2700.,  0.]]
        self.allowFrequencyDependentValues =               [True, False , True ,False,False, False, False, False, False, False]
        self.parameterTipps = ['Youngs Modulus', 'Damping Type <br>1 - scales with eta <br>2 - scales with omega*eta)', 'Damping loss factor', 'Poissons ratio', 'Cross section area (only for beam elements)',
                              'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 
                              'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Density', 'Thickness']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_VIS_ISO_DIR, self).__init__(Id)
        #
        
    def processArguments(self, material_args):
        self.parameterValues = [QLineEdit(str(x)) for x in material_args]

