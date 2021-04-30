#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for AF_LIN_UAF_ISO_DIR           ###
#########################################################

class AF_LIN_UAF_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'ACOUS undamped fluid iso'
        self.type = 'AF_LIN_UAF_ISO_DIR'
        self.toolTip = '<b>Acoustic fluid (undamped) material</b> <br>Basic material model for Helmholtz domain without damping.'
        #
        self.parameterNames =                              [ 'c' , 'rho', 't']
        self.parameterValues = [QLineEdit(str(x)) for x in [ 343.,  1.21,  0.]]
        self.allowFrequencyDependentValues =               [False, False,False]
        self.parameterTipps = ['Speed of sound', 'Density', 'Thickness']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(AF_LIN_UAF_ISO_DIR, self).__init__(Id)
        #


