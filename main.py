################################################
##                                            ##
##   Tool for load application into elpaso    ##
##                 SFB880 A6                  ##
##             Christopher Blech              ##
##                                            ##
################################################

# Load modules
import sys
import os
from lxml import etree
import numpy as np
import h5py
#
from PyQt5.QtWidgets import QApplication, QWidget, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel, QInputDialog, QFileDialog, QMainWindow, QAction
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
#
sys.path.append(os.path.dirname(sys.argv[0]) + './modules')
sys.path.append(os.path.dirname(sys.argv[0]) + './loads')
from standardFunctionsGeneral import buildAk3Framework, readNodes, readElements, readFreqs, writeHdf5Child, deleteHdf5Child, readHdf5
from standardWidgets import sepLine, ak3LoadButton, addButton, loadSelector, messageboxOK, exportButton
from model import model, calculationObject
from vtkWindow import vtkWindow
from graphWindow import graphWindow
from loads import loadInfoBox
#
from planeWave import planeWave
from diffuseField import diffuseField
from timeVarDat import timeVarDat
from tbl import tbl
#
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
        self.setWindowTitle('elPaSo Load Application')
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.ak3path = os.path.dirname(os.path.abspath(__file__)) # where we are
        self.myFont = QFont("Verdana", 12)
        self.myModel = model() # all model information are saved here
        self.myModel.blockInfo.itemClicked.connect(self.update3D) # table containing model information (click event)
        #
        self.setupGui()
        self.show()
        #self.resize(100, 100) # Resize to minimum in order to fit content
        self.statusBar().showMessage('Ready')


    def about(self):
        """
        Message box with information on the program
        """
        msg = messageboxOK('About', 'elPaSo Load Application\n' +
                                    'Institute for Acoustics, Braunschweig\n' +
                                    'Version 0.1 (2019)\n\n' +
                                    'Program to add specific loads to an ak3 input file.\n' +
                                    'Supported loads: plane wave, diffuse field, \ndistributed time domain, turbulent boundary layer')


    def addLoad(self):
        """
        Add the load selected by self.loadSelector (self.addLoadButton click event)
        """
        if self.myModel.name == ' - ':
            messageboxOK('Addition of load not possible', 'Open a model first!')
            return
        if self.loadSelector.currentText() == 'Plane wave':
            self.myModel.loads.append(planeWave(self.ak3path, self.myModel, self.vtkWindow))
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update2D)
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update3D)
        if self.loadSelector.currentText() == 'Diffuse field':
            self.myModel.loads.append(diffuseField(self.ak3path, self.myModel, self.vtkWindow))
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update2D)
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update3D)
        if self.loadSelector.currentText() == 'Distributed time domain load':
            self.myModel.loads.append(timeVarDat(self.ak3path, self.myModel, self.vtkWindow))
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update2D)
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update3D)
        if self.loadSelector.currentText() == 'Turbulent Boundary Layer':
            self.myModel.loads.append(tbl(self.ak3path, self.myModel, self.vtkWindow))
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update2D)
            self.myModel.loads[-1].changeSwitch.stateChanged.connect(self.update3D)
        # Reset new ids for button in order to identify button on next click correctly and reconnect buttons
        for loadNo in range(len(self.myModel.loads)):
            self.myModel.loads[loadNo].removeButton.id = loadNo
            self.myModel.loads[loadNo].removeButton.disconnect()
            self.myModel.loads[loadNo].removeButton.clicked.connect(lambda: self.removeLoad('button'))
        # Refresh layout
        self.loadInfo.clearLayout()
        self.loadInfo.updateLayout(self.myModel.loads)


    def graphWindowClick(self, event):
        """
        User clicks into graph area
        """
        if self.myModel.name != ' - ':
            if event.xdata:
                self.vtkWindow.currentFrequencyStep = np.argmin(abs(np.array(self.myModel.calculationObjects[0].frequencies)-event.xdata))
                self.graphWindow.currentFrequency = self.myModel.calculationObjects[0].frequencies[ self.vtkWindow.currentFrequencyStep ]
                self.update2D()
                self.update3D()


    def loadInput(self):
        """
        Open an ak3 file (self.loadButton click event) and read necessary infirmation out of an hdf5 file
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","ak3 input file (*.ak3)", options=options)
        if fileName:
            self.vtkWindow.clearWindow()
            self.myModel.name = fileName.split('/')[-1].split('.')[0]
            print(fileName.split('.')[0])
            self.myModel.path =  '/'.join(fileName.split('/')[:-1])
            self.myModel.calculationObjects = [] # Only one model can be loaded - every time a file is chosen, the model is reset
            [self.removeLoad(m) for m in range(len(self.myModel.loads))] # All loads are remove, too
            self.myModel.calculationObjects.append(calculationObject('calculation'))
            self.myModel.ak3tree = etree.parse(fileName)
            ##NEW: BINARY FILE LOAD
            self.myModel.binfilename = str(fileName.split('.')[0])+'.hdf5'
            #deleteHdf5Child(['freq', 'mat'], self.myModel.binfilename)
            #self.myModel.binFile = h5py.File(self.myModel.binfilename, 'r+') #readWrite
            ###
            #readNodes(self.myModel.calculationObjects[0], self.myModel.ak3tree)
            #readElems(self.myModel.calculationObjects[0], self.myModel.ak3tree)
            buildAk3Framework(self.myModel.ak3tree)
            readHdf5(self.myModel.calculationObjects[0], self.myModel.binfilename, self.myModel.ak3tree, {'elements':readElements,'nodes':readNodes})
            #readElemsNew(self.myModel.calculationObjects[0], self.myModel.binfilename, self.myModel.ak3tree)
            #readNodesNew(self.myModel.calculationObjects[0], self.myModel.binfilename, self.myModel.ak3tree)
            #print(self.myModel.calculationObjects[0].elems)
            #print(self.myModel.calculationObjects[0].nodes)
            readFreqs(self.myModel)
            self.myModel.updateModelInfo(self.vtkWindow)
            self.vtkWindow.currentFrequencyStep = int(len(self.myModel.calculationObjects[0].frequencies)/2.)
            self.graphWindow.currentFrequency = self.myModel.calculationObjects[0].frequencies[ self.vtkWindow.currentFrequencyStep ]
            self.update2D()
            self.update3D()
            self.statusBar().showMessage('Model loaded')

            self.nodelist = self.myModel.calculationObjects[0].nodes


            ## HOW TO BUILD AN H5PY FILE:
            # f = h5py.File('h5Tester2.hdf5', 'w')
            # for i, group in enumerate(self.myModel.calculationObjects[0].elems):
            #     i = f.create_dataset('/elementsSet/g'+str(i), data=((group[2].tolist())))
            #     i.attrs['type'] = group[0]
            #     i.attrs['groupNo'] = group[1]
            #
            # for n, node in enumerate(self.myModel.calculationObjects[0].nodes):
            #     n = f.create_dataset('/nodesSet/n'+str(n), data=self.myModel.calculationObjects[0].nodes)
            # f.close()



    def removeLoad(self, loadIDToRemove):
        """
        Remove a load from list (removeButton click event)
        """
        # Layout is cleared
        self.loadInfo.clearLayout()
        if loadIDToRemove=='button':
            loadIDToRemove = self.sender().id
        self.myModel.loads[loadIDToRemove].drawCheck.setChecked(0)
        self.vtkWindow.updateLoads(self.myModel.loads)
        self.vtkWindow.resetView()
        self.myModel.loads[loadIDToRemove].clearLayout() # Set widgets to None (remove Button etc)
        self.myModel.loads[loadIDToRemove] = None # Set the pointer to None
        self.myModel.loads.pop(loadIDToRemove) # Remove the entry in list
        self.loadInfo.updateLayout(self.myModel.loads)
        # Reset new ids for button in order to identify button on next click correctly
        for loadNo in range(len(self.myModel.loads)):
            self.myModel.loads[loadNo].removeButton.id = loadNo


    def setupGui(self):
        """
        Initialisation of gui (main window content)
        """
        ### Basic splitting in areas ###
        self.mainLayoutLeft = QVBoxLayout()
        self.mainLayoutRight = QVBoxLayout()
        #
        # CREATE WIDGETS | I - MODEL
        self.label1 = QLabel('Model')
        self.label1.setFont(self.myFont)
        self.loadButton = ak3LoadButton(self.ak3path)
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
        # CREATE WIDGETS | II - LOADS
        self.label2 = QLabel('Loads')
        self.label2.setFont(self.myFont)
        self.loadSelector = loadSelector()
        self.addLoadButton = addButton(self.ak3path)
        self.addLoadButton.clicked.connect(self.addLoad)
        self.loadInfo = loadInfoBox()
        self.clusterSwitch = QCheckBox()
        self.clusterSwitch.setChecked(0)
        self.clusterSwitch.setText('Export for Cluster')
        self.clusterSwitch.setToolTip('Changes file path to convention readable by the cluster  ')
        self.clusterSwitch.stateChanged.connect(self.myModel.toggleCluster)
        self.exportButton = exportButton()
        self.exportButton.clicked.connect(self.myModel.export)
        # ADD TO LAYOUT
        self.loadLayout = QHBoxLayout()
        self.loadLayout.addWidget(self.loadSelector)
        self.loadLayout.addWidget(self.addLoadButton)
        self.loadLayout.addStretch(1)
        self.mainLayoutLeft.addWidget(self.label2)
        self.mainLayoutLeft.addLayout(self.loadLayout)
        self.mainLayoutLeft.addWidget(self.loadInfo)
        self.mainLayoutLeft.setStretchFactor(self.loadInfo, True)
        self.mainLayoutLeft.addWidget(self.clusterSwitch)
        self.mainLayoutLeft.addWidget(self.exportButton)
        #
        # CREATE WIDGETS | III - 3D Window
        self.label3 = QLabel('3D View')
        self.label3.setFont(self.myFont)
        self.vtkWindowParent = QWidget()
        self.vtkWindow = vtkWindow(self.vtkWindowParent, self.ak3path)
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

# main
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = loadGUI()
    sys.exit(app.exec_())
