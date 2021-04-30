#
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy, QLabel, QLineEdit, QCheckBox
from standardWidgets import removeButton, editButton, setupNodeConstraintWindow

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
        #
        self.removeButton = removeButton()
        self.Id = QLineEdit(str(Id))
        self.Id.setToolTip("Id of contraint")
        self.Id.setFixedWidth(50)
        self.label = QLabel(self.type)
        self.label.setToolTip(self.toolTip)
        self.name = QLineEdit('name')
        self.editButton = editButton()
        self.editButton.clicked.connect(self.showEdit)
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
        # ADD TO LAYOUT
        for n in range(len(self.parameterNames)):
            subCheckButton = QCheckBox()
            subWidget = QWidget()
            subLayout = QHBoxLayout(subWidget)
            label = QLabel(self.parameterNames[n])
            label.setFixedWidth(50)
            [subLayout.addWidget(wid) for wid in [subCheckButton, label, self.parameterValues[n]]]
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
   
    def data2hdf5(self, constraintsGroup):
        pass
#        # Exporting the material
#        set = materialsGroup.create_dataset('material' + self.Id.text(), data=[])
#        set.attrs['Id'] = np.uint64(self.Id.text())
#        set.attrs['MaterialType'] = self.type
#        set.attrs['Name'] = self.name.text()
#        for n in range(len(self.parameterNames)): 
#            if self.parameterValues[n].text() == 'freq-dependent':
#                dataList = []
#                table = self.frequencyDependentEdits[n].table
#                for m in range(table.rowCount()):
#                    if table.item(m,0) is not None and table.item(m,1) is not None:
#                        if table.item(m,0).text() and table.item(m,1).text(): 
#                            try:
#                                dataList.append([np.float64(table.item(m,0).text()), np.float64(table.item(m,1).text())])
#                            except:
#                                pass
#                fData = np.array(dataList)
#                fDataSet = materialsGroup.create_dataset('material' + self.Id.text() + '_' + self.parameterNames[n], data=fData)
#                fDataSet.attrs['type'] = 'freq-dependent'
#                fDataSet.attrs['parameter'] = self.parameterNames[n]
#                fDataSet.attrs['colHeader'] = ['frequency', self.parameterNames[n]]
#                fDataSet.attrs['N'] = np.int64(len(dataList))
#                set.attrs[self.parameterNames[n]] = 'material' + self.Id.text() + '_' + self.parameterNames[n]
#            else:
#                set.attrs[self.parameterNames[n]] = float(self.parameterValues[n].text())
            