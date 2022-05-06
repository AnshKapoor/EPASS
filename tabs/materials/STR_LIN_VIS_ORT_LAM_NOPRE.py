#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_VIS_ORT_LAM_NOPRE     ###
#########################################################

class STR_LIN_VIS_ORT_LAM_NOPRE(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear visco ort no prestress'
        self.type = 'STR_LIN_VIS_ORT_LAM_NOPRE'
        self.toolTip = '<b>Structural linear visco-elastic orthotropic</b> <br>Material model according to Hookes law with damping loss factor<br>including separate input for membrane and bending moduli.'
        #
        self.parameterNames =                              ['Ex' ,'Ey','Ez','ExMem','EyMem', 'eta', 'Gxy', 'Gxz', 'Gyz', 'GxyMem', 'nuxy', 'nuxz', 'nuyz', 'nuxyMem', 'rho',  't']
        self.parameterValues = [QLineEdit(str(x)) for x in [ 7.e10,7.e10,  7.e10, 7.e10,   7.e10, 0.001, 2.7e10, 2.7e10, 2.7e10,    2.7e10,    0.3,    0.3,    0.3,       0.3, 2700.,   0.]]
        self.allowFrequencyDependentValues =               [False,False,False,False, False,  True, False, False, False,    False,  False,  False,  False,     False, False,False]
        self.parameterTipps = ['Youngs modulus in x (bending)', 'Youngs modulus in y (bending)', 'Youngs modulus in z (bending)', 'Youngs modulus in x (membrane)', 'Youngs modulus in y (membrane)','Damping loss factor', 
                               'Shear modulus in xy (bending)', 'Shear modulus in xz (bending)', 'Shear modulus in yz (bending)', 'Shear modulus in xy (membrane)',
                               'Poissons ratio xy (bending)', 'Poissons ratio xz (bending)', 'Poissons ratio yz (bending)', 'Poissons ratio xy (membrane)',
                               'Density', 'Thickness']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_VIS_ORT_LAM_NOPRE, self).__init__(Id)
        #


