#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_VIS_ISO_DIR           ###
#########################################################

class STR_LIN_SPR_ORT_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear spring'
        self.type = 'STR_LIN_SPR_ORT_DIR'
        self.toolTip = '<b>Structural damped spring</b> <br>The damping loss factor is used to calculate a discrete complex stiffness.'
        #
        self.parameterNames =                              ['Cx','Cy','Cz','Crx','Cry','Crz','type','eta']
        self.parameterValues = [QLineEdit(str(x)) for x in [  0.,  0.,  0.,   0.,   0.,   0.,     1,   0.]]
        self.allowFrequencyDependentValues =               [False,False,False,False,False,False,False,False]
        self.parameterTipps = ['translational stiffness in x','translational stiffness in y','translational stiffness in z',
                               'rotational stiffness in x','rotational stiffness in y','rotational stiffness in z',
                               'Damping Type <br>1 - scales with eta <br>2 - scales with omega*eta)', 'Damping loss factor']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_SPR_ORT_DIR, self).__init__(Id)
        #
    def processArguments(self, material_args):
        self.parameterValues = [QLineEdit(str(x)) for x in material_args]
