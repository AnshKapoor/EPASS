#
from PyQt5.QtWidgets import QFrame, QPushButton, QSizePolicy, QComboBox, QMessageBox, QGridLayout, QFormLayout, QVBoxLayout, QMainWindow, QWidget, QDialog, QDialogButtonBox, QGroupBox, QProgressDialog
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

# Button to load something
class ak3LoadButton(QPushButton):
    def __init__(self, ak3path):
        super(ak3LoadButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(ak3path + '/pics/load_button.png'))
        self.setIconSize(QSize(50, 50))
        self.setStatusTip('Load model from ak3 file')

# Button to reset something
class resetButton(QPushButton):
    def __init__(self, ak3path):
        super(resetButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(ak3path + '/pics/ref_button.png'))
        self.setIconSize(QSize(20, 20))
        self.setStatusTip('Reset 3D View')
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)

# Button to add something
class addButton(QPushButton):
    def __init__(self, ak3path):
        super(addButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(ak3path + '/pics/add_button.png'))
        self.setIconSize(QSize(20, 20))
        self.setStatusTip('Add selected load')
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)

# Button to remove something
class removeButton(QPushButton):
    def __init__(self, ak3path):
        super(removeButton, self).__init__('')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setIcon(QIcon(ak3path + '/pics/del_button.png'))
        self.setIconSize(QSize(20, 20))
        self.setStatusTip('Remove this load')
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
        self.setStatusTip('Edit this load')
        self.setMaximumWidth(23)
        self.setMaximumHeight(23)
        self.id = 0
        
# Button to export model
class exportButton(QPushButton):
    def __init__(self):
        super(exportButton, self).__init__('Export')
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Export model including created loads.')
        
# Dropdown menu to select a load
class loadSelector(QComboBox):
    def __init__(self):
        super(loadSelector, self).__init__()
        self.setStyleSheet("background-color:rgb(255,255,255)")
        self.setStatusTip('Selected a load')
        self.setFixedWidth(200)
        [self.addItem(load) for load in ['Plane wave', 'Diffuse field', 'Distributed time domain load', 'Turbulent Boundary Layer']]

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
class setupWindow(QDialog):
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
        self.formGroupBoxBlocks = QGroupBox('Blocks')
        self.blockLayout = QFormLayout()
        self.formGroupBoxBlocks.setLayout(self.blockLayout)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.formGroupBoxBlocks)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)
        #