#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_ELA_ISO_DIR           ###
#########################################################

class STR_LIN_ELA_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear elastic iso'
        self.type = 'STR_LIN_ELA_ISO_DIR'
        self.toolTip = '<b>Structural linear elastic isotropic</b> <br>Material model according to Hookes law without damping.'
        #
        self.parameterNames =                              ['E',     'nu',  'A',  'Ix',  'Iy',  'Iz', 'rho',   't', 'Fi']
        self.parameterValues = [QLineEdit(str(x)) for x in [7.e10,     0.3,   0.,    0.,    0.,    0., 2700.,    0.,   0.]]
        self.allowFrequencyDependentValues =               [False , False,False, False, False, False, False, False, False]
        self.parameterTipps = ['Youngs Modulus', 'Poissons ratio', 'Cross section area (only for beam elements)',
                              'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 
                              'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Density', 'Thickness', 'Initial force to prestress element']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_ELA_ISO_DIR, self).__init__(Id)
        #

    def processArguments(self, material_args):
        self.parameterValues = [QLineEdit(str(x)) for x in material_args]



