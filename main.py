################################################
##                                            ##
##   Tool for setting up elpaso input files   ##
##                                            ##
################################################

# Load modules
import sys
import os
import atexit
import numpy as np
import h5py
#
from PyQt5.QtWidgets import QMessageBox, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMainWindow, QAction, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
#
sys.path.append(os.path.dirname(sys.argv[0]) + '/modules')
sys.path.append(os.path.dirname(sys.argv[0]) + '/loads')
sys.path.append(os.path.dirname(sys.argv[0]) + '/tabs')
sys.path.append(os.path.dirname(sys.argv[0]) + '/tabs/materials')
sys.path.append(os.path.dirname(sys.argv[0]) + '/tabs/constraints')
#
from standardFunctionsGeneral import readNodes, readElements, readSetup
from standardWidgets import ak3LoadButton, sepLine, saveAndExitButton, messageboxOK
#
from model import model
from vtkWindow import vtkWindow
from graphWindow import graphWindow
#
from analysisTab import analysisTab
from loadsTab import loadsTab
from materialsTab import materialsTab
from constraintsTab import constraintsTab

# Main class called first
class loadGUI(QMainWindow):
    """
    the main window is constructed here
    """
    def __init__(self):
        """
        initialises main window global attributes
        """
        QMainWindow.__init__(self)
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setupMenu() # Create the menu
        self.setWindowTitle('elPaSo Model Setup')
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.locPath = os.path.dirname(os.path.abspath(__file__)) # where we are
        self.myFont = QFont("Verdana", 12)
        self.myModel = model() # all model information are saved here
        self.myModel.blockInfo.itemClicked.connect(self.update3D) # table containing model information (click event)
        #
        self.setupGui()
        self.show()
        self.loadInput()
        self.statusBar().showMessage('Ready')

    def about(self):
        """
        Message box with information on the program
        """
        messageboxOK('About', 'elPaSo Model Setup\n' +
                                    'Institute for Acoustics, Braunschweig\n' +
                                    'Version 0.1 (2019)\n\n' +
                                    'Program to set up an hdf5 input file for elpaso.\n' +
                                    'Supported loads: plane wave, diffuse field, \ndistributed time domain, turbulent boundary layer')

    def graphWindowClick(self, event):
        """
        User clicks into graph area
        """
        if self.myModel.name != ' - ':
            if event.xdata:
                self.vtkWindow.currentFrequencyStep = np.argmin(abs(np.array(self.myModel.frequencies)-event.xdata))
                self.graphWindow.currentFrequency = self.myModel.frequencies[ self.vtkWindow.currentFrequencyStep ]
                self.update2D()
                self.update3D()

    def loadInput(self):
        """
        Open an hdf5 file (self.loadButton click event)
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","hdf5 file (*.hdf5 *.cub5)", options=options)
        if fileName:
            fileEnding = fileName.split('.')[-1]
            if fileEnding in ['cub5', 'hdf5']:
                # cub5 file from Trelis/coreform opened
                if self.myModel.hdf5File: 
                    self.myModel.hdf5File.close()
                    self.tabLoads.removeAllLoads(self.myModel)
                    self.tabMaterials.removeAllMaterials(self.myModel)
                    self.myModel.reset()
                self.vtkWindow.clearWindow()
                self.myModel.name = fileName.split('/')[-1].split('.')[0]
                self.myModel.path =  '/'.join(fileName.split('/')[:-1])
                self.myModel.fileEnding = fileName.split('.')[-1]
                if fileEnding == 'cub5':
                    success = self.openCub5()
                elif fileEnding == 'hdf5':
                    success = self.openHdf5()
                # Update 2D / 3D windows
                if success:
                    self.myModel.updateModel(self.vtkWindow)
                self.vtkWindow.currentFrequencyStep = int(len(self.myModel.frequencies)/2.)
                self.graphWindow.currentFrequency = self.myModel.frequencies[ self.vtkWindow.currentFrequencyStep ]
                self.update2D()
                self.update3D()
                # Update tabs
                self.updateTabs()
                self.statusBar().showMessage('Model loaded')
            else:
                self.statusBar().showMessage('Unknown file ending (cub5 and hdf5 supported) - no model loaded!')
    
    def openCub5(self): 
        fileName = self.myModel.path + '/' + self.myModel.name + '.cub5'
        newFile = self.myModel.path + '/' + self.myModel.name + '.hdf5'
        reply  = QMessageBox.Yes
        if os.path.isfile(newFile):
            reply = QMessageBox.question(self, 'File existing', 'Overwrite ' + str(newFile) + '?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.myModel.hdf5File = h5py.File(newFile, 'w')
            atexit.register(self.myModel.hdf5File.close)
            # relevant cub5 data is transferred to new hdf5 file
            try: 
                with h5py.File(fileName,'r') as cub5File:
                    readNodes(self.myModel, self.myModel.hdf5File, cub5File)
                    readElements(self.myModel, self.myModel.hdf5File, cub5File)
                    readSetup(self.myModel, self.myModel.hdf5File, cub5File)
                messageboxOK('Ready','cub5 successfully transferred to hdf5 file')
                return 1
            except:
                self.myModel.hdf5File.close()
                os.remove(newFile)
                messageboxOK('Error','cub5 file not transferred')
                return 0
        else:
            messageboxOK('cub5 file selected','HDF5 file ' + self.myModel.name + ' cannot be created as it is already existing!\n Select hdf5 file directly or clean folder.')
            return 0
    
    def openHdf5(self):
        fileName = self.myModel.path + '/' + self.myModel.name + '.hdf5'
        self.myModel.hdf5File = h5py.File(fileName, 'r+')
        atexit.register(self.myModel.hdf5File.close)
        readNodes(self.myModel, self.myModel.hdf5File)
        readElements(self.myModel, self.myModel.hdf5File)
        readSetup(self.myModel, self.myModel.hdf5File)
        messageboxOK('Ready','hdf5 file successfully loaded')
        return 1
        
    def setupGui(self):
        """
        Initialisation of gui (main window content)
        To-Do: Put all the stuff into separate modules and import them.
        One big "GUI" module, which itself loads from smaller modules.
        """
        ### Basic splitting in areas ###
        self.mainLayoutLeft = QVBoxLayout()
        self.mainLayoutRight = QVBoxLayout()
        #
        # CREATE WIDGETS | I - MODEL
        self.label1 = QLabel('Model')
        self.label1.setFont(self.myFont)
        self.loadButton = ak3LoadButton(self.locPath)
        self.loadButton.clicked.connect(self.loadInput)
        self.sepLine1 = sepLine()
        # ADD TO LAYOUT
        self.modelLayout = QHBoxLayout()
        self.loadButtonLayout = QVBoxLayout()
        self.loadButtonLayout.addWidget(self.loadButton)
        self.loadButtonLayout.addStretch(1)
        self.modelLayout.addLayout(self.loadButtonLayout)
        self.modelLayout.addLayout(self.myModel.layout)
        self.modelLayout.addStretch(1)
        self.mainLayoutLeft.addWidget(self.label1)
        self.mainLayoutLeft.addLayout(self.modelLayout)
        self.mainLayoutLeft.addWidget(self.sepLine1)
        #
        # INIT DIFFERENT TABS
        #
        self.tabAnalysis = analysisTab()
        [x.textChanged.connect(self.analysisTabChangeEvent) for x in self.tabAnalysis.changeObjects]
        self.tabLoads = loadsTab()
        self.tabLoads.addLoadButton.clicked.connect(self.addLoadEvent)
        self.tabMaterials = materialsTab()
        self.tabMaterials.addMaterialButton.clicked.connect(self.addMaterialEvent)
        self.tabConstraints = constraintsTab()
        self.tabConstraints.addConstraintButton.clicked.connect(self.addConstraintEvent)
        #self.tabMatCont = trial_mat()     
        #self.tabMaterials = self.tabMatCont#QWidget()
        #self.tabMaterials.titleText = 'Materials'
        #
        self.tabsLeft = QTabWidget()
        [self.tabsLeft.addTab(tab,tab.titleText) for tab in [self.tabAnalysis, self.tabLoads, self.tabMaterials, self.tabConstraints]]

        #self.tabMaterials.tester()
        #self.tabMaterials.saveMat.clicked.connect(self.showSaveEdit)
        
        #
        # CREATE WIDGETS | III - MATERIALS
        # self.labelMat = QLabel('Fill me, please :)')
        # self.labelMat.setFont(self.myFont)
        # # ADD TO LAYOUT
        # self.MatLayout = QVBoxLayout()

        #self.MatLayout.addWidget(self.tabMatCont)
        #self.MatLayout.addWidget(self.labelMat)
        #self.MatLayout.setStretchFactor(self.loadInfo, True)
        #self.tabMaterials.layout = QVBoxLayout(self)
        #self.tabMaterials.setLayout(self.MatLayout)

        # LEFT SIDE EXPORT SETTINGS
        # self.clusterSwitch = QCheckBox()
        # self.clusterSwitch.setChecked(0)
        # self.clusterSwitch.setText('Export for Cluster')
        # self.clusterSwitch.setToolTip('Changes file path to convention readable by the cluster  ')
        # self.clusterSwitch.stateChanged.connect(self.myModel.toggleCluster)
        self.saveAndExitButton = saveAndExitButton()
        self.saveAndExitButton.clicked.connect(self.saveAndExit)

        #  PUT LEFT SIDE TOGETHER
        self.mainLayoutLeft.addWidget(self.tabsLeft, 2)
        # self.mainLayoutLeft.addWidget(self.clusterSwitch)
        self.mainLayoutLeft.addWidget(self.saveAndExitButton)
        
        # CREATE WIDGETS | III - 3D Window
        self.label3 = QLabel('3D View')
        self.label3.setFont(self.myFont)
        self.vtkWindowParent = QWidget()
        self.vtkWindow = vtkWindow(self.vtkWindowParent, self.locPath)
        self.vtkWindow.setMinimumWidth(450)
        self.vtkWindow.setMinimumHeight(250)
        self.sepLine3 = sepLine()
        # ADD TO LAYOUT
        self.mainLayoutRight.addWidget(self.label3)
        self.mainLayoutRight.addLayout(self.vtkWindow.selectionLayout)
        self.mainLayoutRight.addWidget(self.vtkWindow)
        self.mainLayoutRight.setStretchFactor(self.vtkWindow, True)
        self.mainLayoutRight.addWidget(self.sepLine3)
        #
        # CREATE WIDGETS | IV - 2D Graph
        self.label4 = QLabel('Graph')
        self.label4.setFont(self.myFont)
        self.graphWindow = graphWindow()
        self.graphWindow.setMinimumWidth(450)
        self.graphWindow.setMinimumHeight(250)
        self.graphWindow.fig.canvas.mpl_connect('button_press_event', self.graphWindowClick)
        # ADD TO LAYOUT
        self.mainLayoutRight.addWidget(self.label4)
        self.mainLayoutRight.addWidget(self.graphWindow)
        self.mainLayoutRight.setStretchFactor(self.graphWindow, True)
        #
        ### ADD TO MAIN LAYOUT
        self.mainLayout = QHBoxLayout()
        self.mainLayout.addLayout(self.mainLayoutLeft)
        self.mainLayout.addLayout(self.mainLayoutRight)
        self.mainLayout.setStretchFactor(self.mainLayoutLeft, False)
        self.mainLayout.setStretchFactor(self.mainLayoutRight, True)
        self.centralWidget.setLayout(self.mainLayout)
    
    def analysisTabChangeEvent(self):
        try: 
            self.myModel.freqStart = int(self.tabAnalysis.freqStart.text())
            self.myModel.freqSteps = int(self.tabAnalysis.freqSteps.text())
            self.myModel.freqDelta = int(self.tabAnalysis.freqDelta.text())
            self.myModel.updateModelSetup()
        except:
            pass
    
    def addLoadEvent(self):
        success = self.tabLoads.addLoad(self.myModel)
        if success:
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update2D)
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update3D)
            # Reset new ids for button in order to identify button on next click correctly and reconnect buttons
            for loadNo in range(len(self.myModel.loads)):
                self.myModel.loads[loadNo].removeButton.id = loadNo
                self.myModel.loads[loadNo].removeButton.disconnect()
                self.myModel.loads[loadNo].removeButton.clicked.connect(lambda: self.removeLoadEvent('button'))
    
    def removeLoadEvent(self, loadIDToRemove):
        self.tabLoads.removeLoad(loadIDToRemove, self.myModel)
        #self.vtkWindow.updateLoads(self.myModel.loads)
        #self.vtkWindow.resetView()
        # Reset new ids for button in order to identify button on next click correctly
        for loadNo in range(len(self.myModel.loads)):
            self.myModel.loads[loadNo].removeButton.id = loadNo
            
    def addConstraintEvent(self):
        success = self.tabConstraints.addConstraint(self.myModel)
        if success:
            self.myModel.constraints[-1].changeSwitch.stateChanged.connect(self.update2D)
            self.myModel.constraints[-1].changeSwitch.stateChanged.connect(self.update3D)
            # Reset new ids for button in order to identify button on next click correctly and reconnect buttons
            for constraintNo in range(len(self.myModel.constraints)):
                self.myModel.constraints[constraintNo].removeButton.id = constraintNo
                self.myModel.constraints[constraintNo].removeButton.disconnect()
                self.myModel.constraints[constraintNo].removeButton.clicked.connect(lambda: self.removeConstraintEvent('button'))
    
    def removeConstraintEvent(self, constraintIDToRemove):
        self.tabConstraints.removeConstraint(constraintIDToRemove, self.myModel)
        #self.vtkWindow.updateLoads(self.myModel.loads)
        #self.vtkWindow.resetView()
        # Reset new ids for button in order to identify button on next click correctly
        for constraintNo in range(len(self.myModel.constraints)):
            self.myModel.constraints[constraintNo].removeButton.id = constraintNo
    
    def addMaterialEvent(self):
        success = self.tabMaterials.addMaterial(self.myModel)
        if success:
            # Reset new ids for button in order to identify button on next click correctly and reconnect buttons
            for matNo in range(len(self.myModel.materials)):
                self.myModel.materials[matNo].removeButton.id = matNo
                self.myModel.materials[matNo].removeButton.disconnect()
                self.myModel.materials[matNo].removeButton.clicked.connect(lambda: self.removeMaterialEvent('button'))
            self.myModel.updateBlockMaterialSelector()
    
    def removeMaterialEvent(self, matIDToRemove):
        self.tabMaterials.removeMaterial(matIDToRemove, self.myModel)
        # Reset new ids for button in order to identify button on next click correctly
        for matNo in range(len(self.myModel.materials)):
            self.myModel.materials[matNo].removeButton.id = matNo
        self.myModel.updateBlockMaterialSelector()
        
    def setupMenu(self):
        """
        Initialisation of the window menu
        """
        self.menubar = self.menuBar()
        #
        self.fileMenu = self.menubar.addMenu('&File')
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        self.fileMenu.addAction(exitAct)
        #
        self.modelMenu = self.menubar.addMenu('&Model')
        loadAct = QAction('&Load model', self)
        loadAct.setShortcut('Ctrl+L')
        loadAct.setStatusTip('Load model from ak3 file')
        loadAct.triggered.connect(self.loadInput)
        self.modelMenu.addAction(loadAct)
        #
        self.modelMenu = self.menubar.addMenu('&Help')
        helpAct = QAction('&About', self)
        helpAct.setShortcut('Ctrl+H')
        helpAct.setStatusTip('About the program')
        helpAct.triggered.connect(self.about)
        self.modelMenu.addAction(helpAct)

    def update2D(self):
        """
        Update method for 2D graph window
        """
        self.graphWindow.updateWindow(self.myModel)

    def update3D(self):
        """
        Update method for 3D vtk window
        """
        self.vtkWindow.updateWindow(self.myModel)
    
    def updateTabs(self):
        self.tabAnalysis.update(self.myModel)
        self.tabLoads.update(self.myModel)
    
    def saveAndExit(self):
        res = 0
        if self.myModel.hdf5File:
            res = res + self.tabAnalysis.data2hdf5(self.myModel)
            res = res + self.tabLoads.data2hdf5(self.myModel)
            res = res + self.tabMaterials.data2hdf5(self.myModel)
            res = res + self.myModel.data2hdf5()
            if res == 4:
                self.myModel.hdf5File.close()
        if res == 4:
            self.close()
            app.quit()
        else:
            messageboxOK('Problem','Cannot write data to hdf5 - check your input (probably analysis or materials tab)!')

# main
if __name__ == '__main__':
    app = QApplication([])
    gui = loadGUI()
    app.exec_()
    