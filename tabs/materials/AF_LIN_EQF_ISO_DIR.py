#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for AF_LIN_UAF_ISO_DIR           ###
#########################################################

class AF_LIN_EQF_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.type = 'AF_LIN_EQF_ISO_DIR'
        self.toolTip = '<b>Equivalent fluid material</b> <br>Material model for Helmholtz domain with complex and frequency-dependent parameters.'
        #
        self.parameterNames =                              [ 'cf', 'rhof', 't' , 'creal', 'cimag', 'rhoreal', 'rhoimag']
        self.parameterValues = [QLineEdit(str(x)) for x in [ 343.,  1.21 ,  0. , 343.   , 1.7    , 1.21     , 0.       ]]
        self.allowFrequencyDependentValues =               [False,  False,False,    True,    True,      True, True]
        self.parameterTipps = ['Speed of sound', 'Density', 'Thickness', 'Re{Speed of sound}', 'Im{Speed of sound}', 'Re{Density}', 'Im{Density}']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(AF_LIN_EQF_ISO_DIR, self).__init__(Id)
        #
