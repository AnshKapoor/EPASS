#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit, QApplication
from constraints import nodeConstraint
from standardWidgets import progressWindow
import numpy as np

#########################################################

#########################################################
### Constraint Widget for BS_AF_FIELD                 ###
#########################################################

class BC_AF_FIELD(nodeConstraint):
    def __init__(self, Id, myModel):
        #
        self.typeLabel = 'BC_AF_FIELD'
        self.type = 'acoustic' 
        self.toolTip = '<b>Boundary condition for acoustic fluid</b>'
        #
        self.parameterNames =                              [ 'p']
        self.parameterValues = [QLineEdit(str(x)) for x in [   0.]]
        self.parameterTipps = ['Pressure']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(BC_AF_FIELD, self).__init__(Id, myModel)
        #
        
    def data2hdf5(self, constraintsGroup):
        # Exporting the constraint per node
        progWin = progressWindow(len(self.nodePointsIds)-1, 'Exporting ' + self.type + ' constraint ' + str(self.removeButton.id+1))
        for nN, nodeId in enumerate(self.nodePointsIds):
            dataSet = constraintsGroup.create_dataset('nodeConstraint'+str(self.removeButton.id+1) + '_' + str(int(nodeId)), data=[])
            dataSet.attrs['Id'] = np.uint64(str(self.removeButton.id+1) + str(nodeId))
            dataSet.attrs['Name'] = self.name.text()
            dataSet.attrs['NodeId'] = np.uint64(nodeId) # Assign element load to element
            dataSet.attrs['ConstraintType'] = self.type
            dataSet.attrs['MethodType'] = 'FEM'
            # Parameters 
            for n in range(len(self.parameterNames)): 
                dataSet.attrs[self.parameterNames[n]] = np.uint8(self.subCheckButtons[n].isChecked())
                dataSet.attrs['val' + self.parameterNames[n]] = float(self.parameterValues[n].text())
            # Update progress window
            progWin.setValue(nN)
            QApplication.processEvents()

