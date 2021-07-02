#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit, QApplication
from constraints import nodeConstraint
from standardWidgets import progressWindow
import numpy as np

#########################################################

#########################################################
### Constraint Widget for BC_STR_FIELD                ###
#########################################################

class BC_STR_FIELD(nodeConstraint):
    def __init__(self, Id, myModel):
        #
        self.typeLabel = 'BC_STR_FIELD'
        self.type = 'structure' 
        self.toolTip = '<b>Boundary condition for structures</b>'
        #
        self.parameterNames =                              [ 'u1', 'u2', 'u3',  'w1',  'w2',  'w3']
        self.parameterValues = [QLineEdit(str(x)) for x in [   0.,   0.,   0.,    0.,    0.,    0.]]
        self.parameterTipps = ['Displacement in x', 'Displacement in y', 'Displacement in z', 'Rotation around x', 'Rotation around y', 'Rotation around z']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(BC_STR_FIELD, self).__init__(Id, myModel)
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

