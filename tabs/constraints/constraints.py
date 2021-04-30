#
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy, QLabel, QLineEdit, QCheckBox, QApplication
from standardWidgets import removeButton, editButton, setupNodeConstraintWindow, messageboxOK, progressWindow
import numpy as np

# ScrollArea containing loads in bottom left part of program
class constraintInfoBox(QScrollArea):
    def __init__(self):
        super(constraintInfoBox, self).__init__()
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Container widget for scroll area
        self.contWidget = QWidget()
        self.setWidget(self.contWidget)
        self.contLayout = QVBoxLayout(self.contWidget)

    # Clear all content in ScrollArea containing load info
    def clearLayout(self):
        ### Delete all layout content, if existing
        for i in reversed(range(self.contLayout.count())):
            if isinstance(self.contLayout.itemAt(i), QWidgetItem):
                self.contLayout.takeAt(i).widget().setParent(None)
            else:
                self.contLayout.removeItem(self.contLayout.takeAt(i))

    # Renew load content in ScrollArea
    def updateLayout(self, constraints):
        self.clearLayout()
        [self.contLayout.addLayout(con) for con in constraints]
        self.contLayout.addStretch(1)
        self.update()

# General material class
class nodeConstraint(QHBoxLayout):
    def __init__(self, Id, myModel):
        super(nodeConstraint, self).__init__()
        self.myModel = myModel
        self.superType = 'nodeConstraint'
        #
        self.removeButton = removeButton()
        self.Id = QLineEdit(str(Id))
        self.Id.setToolTip("Id of contraint")
        self.Id.setFixedWidth(50)
        self.label = QLabel(self.typeLabel)
        self.label.setToolTip(self.toolTip)
        self.name = QLineEdit('name')
        self.editButton = editButton()
        #
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show constraint in 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        self.initLayout()
        self.initSetupWindow()
        #self.init3DActor()
        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        #
        self.editButton.clicked.connect(self.showEdit)
        var = self.showEdit()
        if var == 0: # is the case if the initial setup window is canceled by the user
            pass
            #self.update3DActor()
    
    def initLayout(self): 
        [self.addWidget(wid) for wid in [self.removeButton, self.Id, self.label, self.name, self.editButton]]
    
    def clearLayout(self):
        """
        Clear all content in material layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))
    
    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupNodeConstraintWindow('Constraint setup')
        self.subCheckButtons = []
        # ADD TO LAYOUT
        for n in range(len(self.parameterNames)):
            self.subCheckButtons.append(QCheckBox())
            subWidget = QWidget()
            subLayout = QHBoxLayout(subWidget)
            label = QLabel(self.parameterNames[n])
            label.setFixedWidth(50)
            [subLayout.addWidget(wid) for wid in [self.subCheckButtons[-1], label, self.parameterValues[n]]]
            self.setupWindow.layout.addWidget(subWidget)
        #
        self.nodesetChecker = []
        for nodeSet in self.myModel.nodeSets:
            self.nodesetChecker.append(QCheckBox())
            self.setupWindow.nodesetLayout.addRow(self.nodesetChecker[-1], QLabel('Nodeset ' + str(nodeSet.attrs['Id'])))
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())
        
    def showEdit(self):
        """
        allows user to set parameters
        """
        self.varSave = [x.text() for x in self.parameterValues]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                # Extract nodes of selected nodesets
                self.findRelevantPoints()
                #self.update3DActor()
                self.switch()
            except: # if input is wrong, show message and reset values
                messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                self.resetValues()
        else:
            self.resetValues()
        return var
        
    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate(self.parameterValues):
            item.setText(self.varSave[n])   
            
    def switch(self):
        """
        Method changing the objects changedSwitch in order to indicate 2D and 3D update
        """
        if self.changeSwitch.isChecked():
            self.changeSwitch.setChecked(0)
        else:
            self.changeSwitch.setChecked(1)
   
    def findRelevantPoints(self):
        """
        Extracts node points from selected nodesets
        """
        self.nodePoints = []
        self.nodePointsIds = []
        relevantNodesets = []
        nodes = self.myModel.nodes
        for p, nodesetCheck in enumerate(self.nodesetChecker):
            nodesetState = nodesetCheck.isChecked()
            if nodesetState==1:
                relevantNodesets.append(self.myModel.nodeSets[p])
        for nodeset in relevantNodesets:
            for nodeIdx in range(len(nodeset[:])):
                self.nodePointsIds.append(nodeset[nodeIdx][0])
                idx = (nodes[:]['Ids']==self.nodePointsIds[-1])
                self.nodePoints.append([nodes[idx]['xCoords'][0], nodes[idx]['yCoords'][0], nodes[idx]['zCoords'][0]])
            self.nodePoints = np.array(self.nodePoints)
        relevantNodesets = []
        nodes = 0
   
    def data2hdf5(self, constraintsGroup):
        pass # To be defined in child!
            