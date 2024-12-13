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
import getopt
#
from PyQt5.QtWidgets import QMessageBox, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMainWindow, QAction, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
#
dirname, filename = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname + '/parser')
sys.path.append(dirname + '/modules')
sys.path.append(dirname + '/loads')
sys.path.append(dirname + '/tabs')
sys.path.append(dirname + '/tabs/materials')
sys.path.append(dirname + '/tabs/constraints')
# parsers
from cParserCub5 import cParserCub5
from cParserElpasoHdf5 import cParserElpasoHdf5
from cParserGmsh import cParserGmsh
from cParserSalomeMed import cParserSalomeMed
from cParserAbaqusInp import cParserAbaqusInp
#
#from standardFunctionsGeneral import readNodes, readElements, readSetup
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
#
from scriptModule import scripter

CMD_MODE = False
if '--cmd' in sys.argv:
    CMD_MODE = True

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

    def deploy(self):
        self.show()
        self.loadInputWin()
        self.statusBar().showMessage('Ready')

    def about(self):
        """
        Message box with information on the program
        """
        messageboxOK('About', 'elPaSo Model Setup\n' +
                                    'Institute for Acoustics, Braunschweig\n' +
                                    'Version 1.0 (2021)\n\n' +
                                    'Program to set up an hdf5 input file for elpaso.\n')

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

    def loadInputWin(self):
        """
        Open an hdf5 file (self.loadButton click event)
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","preprocessor supported files (*.hdf5 *.cub5 *.msh *.inp *.med)", options=options)
        if fileName:
            fileEnding = fileName.split('.')[-1]
            if fileEnding in ['cub5', 'hdf5','msh','inp','med']:
                # cub5 file from Trelis/coreform opened
                if self.myModel.hdf5File: 
                    self.myModel.hdf5File.close()
                    self.tabLoads.removeAllLoads(self.myModel)
                    self.tabMaterials.removeAllMaterials(self.myModel)
                    self.myModel.reset()
                self.vtkWindow.clearWindow()
                fileName = fileName.replace("\\", "/")
                self.myModel.name = fileName.split('/')[-1].split('.')[0]
                self.myModel.path =  '/'.join(fileName.split('/')[:-1])
                self.myModel.fileEnding = fileName.split('.')[-1]
                
                if fileEnding == 'cub5':
                    self.myModel.input = 'cub5'
                elif fileEnding == 'hdf5':
                    self.myModel.input = 'elPaSo'
                elif fileEnding == 'msh':
                    self.myModel.input = 'Gmsh'
                elif fileEnding == 'inp':
                    self.myModel.input = 'Abaqus'
                elif fileEnding == 'med':
                    self.myModel.input = 'Salome'

                success = self.openMeshData()
                # Update 2D / 3D windows
                if success:
                    self.myModel.updateModel(self.vtkWindow)
                    self.myModel.interFaceElemAddButton.clicked.connect(self.interfaceElemDialogEvent)
                    self.myModel.orthoCheckerButton.clicked.connect(self.orthoCheckerEvent)
                self.vtkWindow.currentFrequencyStep = int(len(self.myModel.frequencies)/2.)
                scaleFactor = max( [abs(max(self.myModel.nodes[:]['xCoords'])-min(self.myModel.nodes[:]['xCoords'])), abs(max(self.myModel.nodes[:]['yCoords'])-min(self.myModel.nodes[:]['yCoords'])), abs(max(self.myModel.nodes[:]['zCoords'])-min(self.myModel.nodes[:]['zCoords']))] )
                self.vtkWindow.defineAxisLength(scaleFactor)
                self.graphWindow.currentFrequency = self.myModel.frequencies[ self.vtkWindow.currentFrequencyStep ]
                self.update2D()
                self.update3D()
                # Update tabs
                self.updateTabs()
                self.statusBar().showMessage('Model loaded')
            else:
                self.statusBar().showMessage('Unknown file ending - no model loaded!')
    
    # @brief general function to open mesh data
    def openMeshData(self): 
        newFile = self.myModel.path + '/' + self.myModel.name + '.hdf5'

        reply  = QMessageBox.Yes
        if os.path.isfile(newFile):
            reply = QMessageBox.question(self, 'File existing', 'Overwrite ' + str(newFile) + '?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.myModel.input == 'cub5':
                fileName = self.myModel.path + '/' + self.myModel.name + '.cub5'
                self.myModel.hdf5File = h5py.File(newFile, 'w')
                parser = cParserCub5(fileName)
            elif self.myModel.input == 'elPaSo':
                fileName = self.myModel.path + '/' + self.myModel.name + '.hdf5'
                self.myModel.hdf5File = h5py.File(newFile, 'r+')
                parser = cParserElpasoHdf5(fileName)
            elif self.myModel.input == 'Salome':
                fileName = self.myModel.path + '/' + self.myModel.name + '.med'
                self.myModel.hdf5File = h5py.File(newFile, 'w')
                parser = cParserSalomeMed(fileName)
            elif self.myModel.input == 'Gmsh':
                fileName = self.myModel.path + '/' + self.myModel.name + '.msh'
                self.myModel.hdf5File = h5py.File(newFile, 'w')
                parser = cParserGmsh(fileName)
            elif self.myModel.input == 'Abaqus':
                fileName = self.myModel.path + '/' + self.myModel.name + '.inp'
                self.myModel.hdf5File = h5py.File(newFile, 'w')
                parser = cParserAbaqusInp(fileName)
            else:
                messageboxOK('Error',f'Input mode {self.myModel.input} not recognised')
                return 0

            atexit.register(self.myModel.hdf5File.close)
            parser.readElements(self.myModel)
            parser.readNodes(self.myModel)
            parser.readSetup(self.myModel)
            # relevant cub5 data is transferred to new hdf5 file
            try: 
                # parser.readElements(self.myModel)
                # parser.readNodes(self.myModel)
                # parser.readSetup(self.myModel)
                messageboxOK('Ready',f'{self.myModel.input} file successfully transferred to hdf5 file')
                return 1
            except:
                self.myModel.hdf5File.close()
                os.remove(newFile)
                messageboxOK('Error',f'{self.myModel.input} file not transferred')
                return 0
        else:
            messageboxOK(f'{self.myModel.input} file selected','HDF5 file ' + self.myModel.name + ' cannot be created as it is already existing!\n Select hdf5 file directly or clean folder.')
            return 0
            
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
        self.loadButton = ak3LoadButton()
        self.loadButton.clicked.connect(self.loadInputWin)
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
        self.tabMaterials.importMaterialButton.clicked.connect(self.importMaterialsEvent)
        self.tabConstraints = constraintsTab()
        self.tabConstraints.addConstraintButton.clicked.connect(self.addConstraintEvent)
        #
        self.tabsLeft = QTabWidget()
        [self.tabsLeft.addTab(tab,tab.titleText) for tab in [self.tabAnalysis, self.tabLoads, self.tabMaterials, self.tabConstraints]]
        #
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
    

    def setFrequency(self, start, steps, delta):
        self.tabAnalysis.freqStart.setText(str(start))
        self.tabAnalysis.freqSteps.setText(str(steps))
        self.tabAnalysis.freqDelta.setText(str(delta))
        self.analysisTabChangeEvent()

    def addLoad(self, load_type, load_args):
        self.tabLoads.addLoad(self.myModel, load_type)
        load = self.myModel.loads[-1]
        load.processArguments(load_args)

    def addMaterial(self, material_type, material_args):
        self.tabMaterials.addMaterial(self.myModel, material_type)
        material = self.myModel.materials[-1]
        material.processArguments(material_args)
        self.updateMaterials()
        self.myModel.updateModel(self.vtkWindow)

    def addConstraint(self, contraint_type, constraint_args):
        self.tabConstraints.addConstraint(self.myModel, contraint_type)
        constraint = self.myModel.constraints[-1]
        constraint.processArguments(constraint_args)

    def setBlockProperties(self, block_dict):
        n_blocks_dict = len(block_dict.keys())
        n_blocks_model = len(self.myModel.elems)
        assert n_blocks_dict == n_blocks_model, f'Assigned properties for {n_blocks_dict} blocks, model has {n_blocks_model} blocks.'

        for block_idx, block in enumerate(block_dict.keys()):
            self.myModel.blockElementTypeSelectors[block_idx].setCurrentText(block_dict[block][0])
            self.myModel.blockMaterialSelectors[block_idx].setCurrentText(str(block_dict[block][1]))
            self.myModel.blockOrientationSelectors[block_idx].setCurrentText(block_dict[block][2])

        
    def analysisTabChangeEvent(self):
        try: 
            self.myModel.freqStart = float(self.tabAnalysis.freqStart.text())
            self.myModel.freqSteps = int(self.tabAnalysis.freqSteps.text())
            self.myModel.freqDelta = float(self.tabAnalysis.freqDelta.text())
            self.myModel.updateModelSetup()
        except:
            self.myModel.updateModelSetup(True)
    
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
        self.myModel.loads[self.sender().id].drawCheck.setChecked(0)
        self.vtkWindow.updateLoads(self.myModel.loads)
        self.vtkWindow.resetView()
        self.tabLoads.removeLoad(self.myModel)
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
            self.updateMaterials()
    
    def importMaterialsEvent(self):
        success = self.tabMaterials.importMaterial(self.myModel)
        if success:
            self.updateMaterials()
            self.myModel.autoAssignBlockMaterialSelectors()
   
    def removeMaterialEvent(self, matIDToRemove):
        self.tabMaterials.removeMaterial(matIDToRemove, self.myModel)
        # Reset new ids for button in order to identify button on next click correctly
        for matNo in range(len(self.myModel.materials)):
            self.myModel.materials[matNo].removeButton.id = matNo
        self.myModel.updateBlockMaterialSelector()
   
    def updateMaterials(self):# Reset new ids for button in order to identify button on next click correctly and reconnect buttons
        for matNo in range(len(self.myModel.materials)):
            self.myModel.materials[matNo].removeButton.id = matNo
            self.myModel.materials[matNo].removeButton.disconnect()
            self.myModel.materials[matNo].removeButton.clicked.connect(lambda: self.removeMaterialEvent('button'))
        self.myModel.updateBlockMaterialSelector()
    
    def interfaceElemDialogEvent(self):
        self.myModel.interfaceElemDialog(self.vtkWindow)
    
    def orthoCheckerEvent(self):
        self.myModel.showShellOrientations(self.vtkWindow)
        
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
        loadAct.triggered.connect(self.loadInputWin)
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
            res = res + self.tabConstraints.data2hdf5(self.myModel)
            res = res + self.myModel.data2hdf5()
            
            if res == 5:
                self.myModel.hdf5File.close()
        if res == 5:
            self.close()
            app.quit()
        else:
            messageboxOK('Problem','Cannot write data to hdf5 - check your input (probably analysis or materials tab)!')

# main
if __name__ == '__main__':
    app = QApplication([])
    gui = loadGUI()

    opts, args = getopt.getopt(sys.argv[1:],'',['cmd', 'script='])
    gui_mode = True
    for o,a in opts:
        if o in ("-c", "--cmd"):
            gui_mode = False

    if gui_mode:
        gui.deploy()
        app.exec_()
    else:
        CMD_MODE = True
        print('Tool in scripting mode...')

        script_filename = 'NA'
        for o,a in opts:
            if o in ("-s", "--script"):
                script_filename = a

        myScripter = scripter(script_filename)
        myScripter.executeScript(gui)
        gui.saveAndExit()
        
