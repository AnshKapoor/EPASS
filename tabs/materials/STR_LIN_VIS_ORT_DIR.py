#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_VIS_ISO_DIR           ###
#########################################################

class STR_LIN_VIS_ORT_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear visco ort'
        self.type = 'STR_LIN_VIS_ORT_DIR'
        self.toolTip = '<b>Structural linear visco-elastic orthotropic</b> <br>Material model according to Hookes law with damping loss factor.'
        #
        self.parameterNames =                              ['Ex' ,'Ey','Ez', 'eta', 'Gxy', 'Gxz', 'Gyz', 'nuxy', 'nuxz', 'nuyz', 'rho', 't']
        self.parameterValues = [QLineEdit(str(x)) for x in [ 7.e9,7.e9,7.e9, 0.001, 2.7e9, 2.7e9, 2.7e9,    0.3,    0.3,    0.3, 2700.,  0.]]
        self.allowFrequencyDependentValues =               [False,False,False,True, False, False, False,  False,  False,  False, False, False]
        self.parameterTipps = ['Youngs Modulus', 'Damping Type <br>1 - scales with eta <br>2 - scales with omega*eta)', 'Damping loss factor', 'Poissons ratio', 'Cross section(only for beam elements)',
                              'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 
                              'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 'Moment of inertia (only for BeamBernoulli and BeamTimoshenko)', 
                              'Density', 'Thickness', 'Initial force to prestress element']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_VIS_ORT_DIR, self).__init__(Id)
        #


