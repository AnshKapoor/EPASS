#
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy, QLabel, QLineEdit
import numpy as np
from standardWidgets import removeButton, editButton, setupMaterialWindow, setupTable

# ScrollArea containing loads in bottom left part of program
class matInfoBox(QScrollArea):
    def __init__(self):
        super(matInfoBox, self).__init__()
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
    def updateLayout(self, materials):
        self.clearLayout()
        [self.contLayout.addLayout(mat) for mat in materials]
        self.contLayout.addStretch(1)
        self.update()

# General material class
class material(QHBoxLayout):
    def __init__(self, Id):
        super(material, self).__init__()
        #
        self.removeButton = removeButton()
        self.Id = QLineEdit(str(Id))
        self.Id.setToolTip("Id of Material")
        self.Id.setFixedWidth(50)
        self.label = QLabel(self.type)
        self.label.setToolTip(self.toolTip)
        self.name = QLineEdit('name')
        self.editButton = editButton()
        self.editButton.clicked.connect(self.showEdit)
        self.frequencyDependentEdits = [[] for n in range(len(self.parameterNames))]
        #
        self.initLayout()
        self.initSetupWindow()
    
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
        self.setupWindow = setupMaterialWindow('Material setup')
        # ADD TO LAYOUT
        for n in range(len(self.parameterNames)):
            if self.allowFrequencyDependentValues[n]:
                self.frequencyDependentEdits[n] = setupTable(['Frequency', self.parameterNames[n]])
                subEditButton = editButton()
                subEditButton.id = n
                subEditButton.clicked.connect(self.frequencyDependentEditEvent)
            else:
                subEditButton = QLabel('')
                subEditButton.setFixedWidth(23)
            subWidget = QWidget()
            subLayout = QHBoxLayout(subWidget)
            label = QLabel(self.parameterNames[n])
            label.setFixedWidth(50)
            [subLayout.addWidget(wid) for wid in [label, self.parameterValues[n], subEditButton]]
            self.setupWindow.layout.addWidget(subWidget)
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())
    
    def frequencyDependentEditEvent(self):
        self.frequencyDependentEdits[self.sender().id].exec_()
        table = self.frequencyDependentEdits[self.sender().id].table
        entries = False
        for m in range(table.rowCount()):
            for n in range(table.columnCount()):
                if table.item(m,n) is not None:
                    if table.item(m,n).text(): 
                        entries = True
        if entries: # Table is filled
            self.parameterValues[self.sender().id].setEnabled(False)
            self.parameterValues[self.sender().id].setText('freq-dependent')
        else: # Table is empty
            self.parameterValues[self.sender().id].setEnabled(True)
    
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
    
    def data2hdf5(self, materialsGroup):
        # Exporting the material
        set = materialsGroup.create_dataset('material' + self.Id.text(), data=[])
        set.attrs['Id'] = np.uint64(self.Id.text())
        set.attrs['MaterialType'] = self.type
        set.attrs['Name'] = self.name.text()
        for n in range(len(self.parameterNames)): 
            set.attrs[self.parameterNames[n]] = float(self.parameterValues[n].text())
            