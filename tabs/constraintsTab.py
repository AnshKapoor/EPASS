from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QFont
from standardWidgets import constraintTypeSelector, addButton, messageboxOK
from constraints import constraintInfoBox

from BC_STR_FIELD import BC_STR_FIELD

class constraintsTab(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.tabLayout = QVBoxLayout(self)
        self.subLayouts = []
        self.changeObjects = []
        self.myFont = QFont("Verdana", 12)
        self.titleText = "Constraints"
        #
        self.typeLabel = QLabel('Constraint Type')
        self.constraintSelector = constraintTypeSelector()
        self.addConstraintButton = addButton()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.typeLabel)
        self.subLayouts[-1].addWidget(self.constraintSelector)
        self.subLayouts[-1].addWidget(self.addConstraintButton)
        self.subLayouts[-1].addStretch()
        #
        self.constraintInfo = constraintInfoBox()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].setStretchFactor(self.constraintInfo, True)
        self.subLayouts[-1].addWidget(self.constraintInfo)
        #
        [self.tabLayout.addLayout(layout) for layout in self.subLayouts]
        
    def addConstraint(self, myModel):
        """
        Add the constraint selected by self.constraintSelector (self.addConstraintButton click event)
        """
        if myModel.hdf5File:
            if self.constraintSelector.currentText() == 'BC | Structure | Fieldvalue':
                myModel.constraints.append(BC_STR_FIELD(self.getFreeId(myModel.constraints), myModel))
            # Refresh layout
            self.constraintInfo.updateLayout(myModel.constraints)
            return 1
        else:
            messageboxOK('Addition of constraint not possible', 'Open a model first!')
            return 0
    
    def getFreeId(self, constraints):
        Idlist = []
        if not constraints: # When no constraint is defined
            return '1'
        for con in constraints:
            Idlist += [str(con.Id.text())]
        for n in range(1, len(Idlist)+1):
            if str(n) not in Idlist:
                return str(n)
        return str(len(Idlist)+1)
    
    def removeConstraint(self, constraintIDToRemove, myModel):
        """
        Remove a constraint from model (removeButton click event)
        """
        # Layout is cleared
        self.constraintInfo.clearLayout()
        if constraintIDToRemove=='button':
            constraintIDToRemove = self.sender().id
        myModel.constraints[constraintIDToRemove].drawCheck.setChecked(0)
        myModel.constraints[constraintIDToRemove].clearLayout() # Set widgets to None (remove Button etc)
        myModel.constraints[constraintIDToRemove] = None # Set the pointer to None
        myModel.constraints.pop(constraintIDToRemove) # Remove the entry in list
        self.constraintInfo.updateLayout(myModel.constraints)
        
    def removeAllConstraints(self, myModel):
        """
        Remove all constraints from model
        """
        # Layout is cleared
        self.constraintInfo.clearLayout()
        for n in range(len(myModel.constraints)-1,-1,-1):
            myModel.constraints[n].drawCheck.setChecked(0)
            myModel.constraints[n].clearLayout() # Set widgets to None (remove Button etc)
            myModel.constraints[n] = None # Set the pointer to None
            myModel.constraints.pop(n) # Remove the entry in list
        self.constraintInfo.updateLayout(myModel.constraints)
        
    def update(self, myModel):
        self.constraintInfo.updateLayout(myModel.constraints)
    
    def data2hdf5(self, myModel): 
        try:
            # Write load data to hdf5 file
            if not 'ElemConstraints' in myModel.hdf5File.keys():
                myModel.hdf5File.create_group('ElemConstraints')
            elemConstraintsGroup = myModel.hdf5File['ElemConstraints']
            for dataSet in elemConstraintsGroup.keys():
                del elemConstraintsGroup[dataSet]
            #
            if not 'NodeConstraints' in myModel.hdf5File.keys():
                myModel.hdf5File.create_group('NodeConstraints')
            nodeConstraintsGroup = myModel.hdf5File['NodeConstraints']
            for dataSet in nodeConstraintsGroup.keys():
                del nodeConstraintsGroup[dataSet]
            #
            for constraint in myModel.constraints:
                if constraint.superType == 'elemConstraint':
                    constraint.data2hdf5(elemConstraintsGroup)
                elif constraint.superType == 'nodeConstraint':
                    constraint.data2hdf5(nodeConstraintsGroup)
                else: 
                    pass
#            #
            return 1
        except:
            return 0
    