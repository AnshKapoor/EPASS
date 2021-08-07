#
import os
#
from PyQt5.QtWidgets import QFrame, QPushButton, QSizePolicy, QComboBox, QMessageBox, QFormLayout, QVBoxLayout, QDialog, QDialogButtonBox, QGroupBox, QProgressDialog, QTableWidget, QScrollArea, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

# Horizontal line
class sepLine(QFrame):
    def __init__(self):
        super(sepLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.setLineWidth(1)
        self.setFixedHeight(5)

# Vertical line
class sepLineV(QFrame):
    def __init__(self):
        super(sepLineV, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.setLineWidth(1)
        #self.setFixedHeight(5)

# Button to load something
class ak3LoadButton(QPushButton):
    def __init__(self):
        super(ak3LoadButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(os.path.dirname(__file__) + '/../pics/load_button.png'))
        self.setIconSize(QSize(50, 50))
        self.setStatusTip('Load model from ak3 file')

# Button to reset something
class resetButton(QPushButton):
    def __init__(self):
        super(resetButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(os.path.dirname(__file__) + '/../pics/ref_button.png'))
        self.setIconSize(QSize(20, 20))
        self.setStatusTip('Reset 3D View')
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)

# Button to save something
class saveButton(QPushButton):
    def __init__(self):
        super(saveButton, self).__init__('Save')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        #self.setIcon(QIcon(ak3path + '/pics/ref_button.png'))
        #self.setIconSize(QSize(20, 20))
        self.setStatusTip('Save Frequencies')
        self.setMaximumWidth(46)
        self.setMaximumHeight(23)

# Button to add something
class addButton(QPushButton):
    def __init__(self):
        super(addButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(os.path.dirname(__file__) + '/../pics/add_button.png'))
        self.setIconSize(QSize(20, 20))
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)

# Button to remove something
class removeButton(QPushButton):
    def __init__(self):
        super(removeButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(os.path.dirname(__file__) + '/../pics/del_button.png'))
        self.setIconSize(QSize(20, 20))
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)
        self.id = 0

# Button to remove something
class editButton(QPushButton):
    def __init__(self):
        super(editButton, self).__init__('...')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        #self.setIcon(QIcon(ak3path + '/pics/del_button.png'))
        #self.setIconSize(QSize(20, 20))
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)
        self.id = 0

# Button to export model
class saveAndExitButton(QPushButton):
    def __init__(self):
        super(saveAndExitButton, self).__init__('Save and Exit')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Saves the model in hdf5 and quits program.')

# Dropdown menu to select an analysis type
class analysisTypeSelector(QComboBox):
    def __init__(self):
        super(analysisTypeSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Select an anylsis type')
        self.availableTypes = ['frequency']#['static', 'eigen', 'frequency', 'time']
        self.setFixedWidth(200)
        [self.addItem(type) for type in self.availableTypes]
    
    def changeTo(self, analysisType):
        try: 
            self.setCurrentIndex(self.availableTypes.index(analysisType))
        except:
            pass
    
# Dropdown menu to select a solver type
class solverTypeSelector(QComboBox):
    def __init__(self):
        super(solverTypeSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Select a routine')
        self.availableTypes = ['elpasoC']#['elpaso', 'elpasoC']
        self.setFixedWidth(200)
        [self.addItem(type) for type in self.availableTypes]
    
    def changeTo(self, solverType):
        try: 
            self.setCurrentIndex(self.availableTypes.index(solverType))
        except:
            pass

# Dropdown menu to select a plane
class planeSelector(QComboBox):
    def __init__(self):
        super(planeSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Select a plane')
        self.availableTypes = ['x-plane','y-plane','z-plane']
        self.setFixedWidth(200)
        [self.addItem(type) for type in self.availableTypes]
    
    def changeTo(self, solverType):
        try: 
            self.setCurrentIndex(self.availableTypes.index(solverType))
        except:
            pass

# Dropdown menu to select a load
class loadTypeSelector(QComboBox):
    def __init__(self):
        super(loadTypeSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Select a load')
        self.availableTypes = ['Point force', 'Plane wave', 'Normal velocity', 'Turbulent Boundary Layer', 'Distributed time domain load']#, 'Diffuse field', 'Turbulent Boundary Layer']
        self.setFixedWidth(200)
        [self.addItem(load) for load in self.availableTypes]
    
    def changeTo(self, loadType):
        try: 
            self.setCurrentIndex(self.availableTypes.index(loadType))
        except:
            pass
            
# Dropdown menu to select a material
class materialTypeSelector(QComboBox):
    def __init__(self):
        super(materialTypeSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Select a material')
        self.availableTypes = ['STRUCT linear elastic iso', 'STRUCT linear visco iso', 'STRUCT linear visco ort', 'STRUCT linear visco ort pre', 'STRUCT linear spring', 'STRUCT linear pointmass', 'ACOUS undamped fluid iso', 'ACOUS damped fluid iso', 'ACOUS equivalent fluid iso']#, 'Orthotropic', 'viscoorthotropic', 'Fluid', 'Viscoelastic', 'CLD:Cremer/Heckl', 'CLD:Ross/Kerwin/Ungar', 'Fluidloss', 'EquivalentFluidDirect', 'Cloaking', 'Poro3d', 'Viscofreq', 'Viscofreqparam', 'Spring','Pointmass']
        self.setFixedWidth(200)
        [self.addItem(mat) for mat in self.availableTypes]
    
    def changeTo(self, matType):
        try: 
            self.setCurrentIndex(self.availableTypes.index(matType))
        except:
            pass

# Dropdown menu to select a load
class constraintTypeSelector(QComboBox):
    def __init__(self):
        super(constraintTypeSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Select a constraint')
        self.availableTypes = ['BC | Structure | Fieldvalue']
        self.setFixedWidth(200)
        [self.addItem(load) for load in self.availableTypes]
    
    def changeTo(self, constraintType):
        try: 
            self.setCurrentIndex(self.availableTypes.index(constraintType))
        except:
            pass

# A standard message box with ok button only
class messageboxOK(QMessageBox):
    def __init__(self, title, text):
        super(messageboxOK, self).__init__()
        self.setWindowTitle(title)
        self.setIcon(QMessageBox.Information)
        self.setText(text)
        self.setStandardButtons(QMessageBox.Ok)
        self.exec_()

# Progress window
class progressWindow(QProgressDialog):
    def __init__(self, length, title='Processing...'):
        super(QProgressDialog, self).__init__(title, "Cancel", 0, length)
        self.setWindowModality(Qt.WindowModal)
        self.show()

# Basic setup window
class addInterfaceWindow(QDialog):
    def __init__(self):
        super(QDialog, self).__init__()
        self.setWindowTitle('Create an interface')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # Block selection
        self.contWidget = QWidget()
        self.formGroupBoxBlocks = QScrollArea()
        self.formGroupBoxBlocks.setWidget(self.contWidget)
        self.formGroupBoxBlocks.setWidgetResizable(True)
        self.formGroupBoxBlocks.setMaximumHeight(400)
        self.blockLayout = QVBoxLayout(self.contWidget)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBoxBlocks)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

# Basic setup window
class setupNodeLoadWindow(QDialog):
    def __init__(self, subTitle):
        super(QDialog, self).__init__()
        self.setWindowTitle('Edit load')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # setup
        self.formGroupBox = QGroupBox(subTitle)
        self.layout = QFormLayout()
        self.formGroupBox.setLayout(self.layout)
        # Nodeset selection
        self.formGroupBoxNodesets = QGroupBox('Nodesets')
        self.nodesetLayout = QFormLayout()
        self.formGroupBoxNodesets.setLayout(self.nodesetLayout)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.formGroupBoxNodesets)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

# Basic setup window
class setupLoadWindow(QDialog):
    def __init__(self, waveType):
        super(QDialog, self).__init__()
        self.setWindowTitle('Edit load')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # setup
        self.formGroupBox = QGroupBox(waveType)
        self.layout = QFormLayout()
        self.formGroupBox.setLayout(self.layout)
        # block selection
        self.contWidget = QWidget()
        self.formGroupBoxBlocks = QScrollArea()
        self.formGroupBoxBlocks.setWidget(self.contWidget)
        self.formGroupBoxBlocks.setWidgetResizable(True)
        self.formGroupBoxBlocks.setMaximumHeight(400)
        self.blockLayout = QVBoxLayout(self.contWidget)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.formGroupBoxBlocks)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

# Basic setup window
class setupMaterialWindow(QDialog):
    def __init__(self, subtitle):
        super(QDialog, self).__init__()
        self.setWindowTitle('Edit material')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # setup
        self.formGroupBox = QGroupBox(subtitle)
        self.layout = QVBoxLayout()
        self.formGroupBox.setLayout(self.layout)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

# Basic setup window
class setupNodeConstraintWindow(QDialog):
    def __init__(self, waveType):
        super(QDialog, self).__init__()
        self.setWindowTitle('Edit constraint')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # setup
        self.formGroupBox = QGroupBox(waveType)
        self.layout = QFormLayout()
        self.formGroupBox.setLayout(self.layout)
        # Nodeset selection
        self.formGroupBoxNodesets = QGroupBox('Nodesets')
        self.nodesetLayout = QFormLayout()
        self.formGroupBoxNodesets.setLayout(self.nodesetLayout)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.formGroupBoxNodesets)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

class setupTable(QDialog):
    def __init__(self, header):
        QDialog.__init__(self)
        self.setWindowTitle('Input frequency dependent data')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        #
        self.table = QTableWidget()
        self.table.setColumnCount(len(header))
        self.table.setRowCount(10)
        self.table.setHorizontalHeaderLabels(header)
        #self.setData()
        #self.resizeColumnsToContents()
        #self.resizeRowsToContents()
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.table)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
 
    # def setData(self): 
        # horHeaders = []
        # for n, key in enumerate(sorted(self.data.keys())):
            # horHeaders.append(key)
            # for m, item in enumerate(self.data[key]):
                # newitem = QTableWidgetItem(item)
                # self.setItem(m, n, newitem)
        # self.setHorizontalHeaderLabels(horHeaders)


class editWindowBasic(QDialog):
    def __init__(self, Type):
        super(QDialog, self).__init__()
        self.setWindowTitle('Edit '+Type)

        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.formGroupBox = QGroupBox(Type)
        self.layout = QFormLayout()
        self.formGroupBox.setLayout(self.layout)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
