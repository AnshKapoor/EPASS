#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_VIS_ORT_DIR           ###
#########################################################

class STR_LIN_VIS_ORT_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear visco ort'
        self.type = 'STR_LIN_VIS_ORT_DIR'
        self.toolTip = '<b>Structural linear visco-elastic orthotropic</b> <br>Material model according to Hookes law with damping loss factor.'
        #
        self.parameterNames =                              ['Ex' ,'Ey','Ez', 'eta', 'Gxy', 'Gxz', 'Gyz', 'nuxy', 'nuxz', 'nuyz', 'rho', 't']
        self.parameterValues = [QLineEdit(str(x)) for x in [ 7.e10,7.e10,7.e10, 0.001, 2.7e10, 2.7e10, 2.7e10,    0.3,    0.3,    0.3, 2700.,  0.]]
        self.allowFrequencyDependentValues =               [False,False,False,True, False, False, False,  False,  False,  False, False, False]
        self.parameterTipps = ['Youngs modulus in x', 'Youngs modulus in y', 'Youngs modulus in z', 'Damping loss factor', 
                               'Shear modulus in xy', 'Shear modulus in xz', 'Shear modulus in yz', 
                               'Poissons ratio xy', 'Poissons ratio xz', 'Poissons ratio yz', 
                               'Density', 'Thickness']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_VIS_ORT_DIR, self).__init__(Id)
        #


