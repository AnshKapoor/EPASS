#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from constraints import nodeConstraint

#########################################################

#########################################################
### Material Widget for AF_LIN_UAF_ISO_DIR           ###
#########################################################

class BC_STR_FIELD(nodeConstraint):
    def __init__(self, Id, myModel):
        #
        self.type = 'BC_STR_FIELD'
        self.toolTip = '<b>Boundary condition for structures</b>'
        #
        self.parameterNames =                              [ 'u' , 'v', 'w']
        self.parameterValues = [QLineEdit(str(x)) for x in [   0.,  0.,  0.]]
        self.parameterTipps = ['Displacement in x', 'Displacement in y', 'Displacement in z']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(BC_STR_FIELD, self).__init__(Id, myModel)
        #


