#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material

#########################################################

#########################################################
### Material Widget for STR_LIN_VIS_ISO_DIR           ###
#########################################################

class STR_LIN_MAS_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.typeLabel = 'STRUCT linear pointmass'
        self.type = 'pointmass'
        self.toolTip = '<b>Structural pointmass</b>'
        #
        self.parameterNames =                              ['M']
        self.parameterValues = [QLineEdit(str(x)) for x in [0.]]
        self.allowFrequencyDependentValues =               [False]
        self.parameterTipps = ['Mass']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(STR_LIN_MAS_ISO_DIR, self).__init__(Id)
        #


