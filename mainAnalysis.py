################################################
##                                            ##
##   Tool for analysis of results             ##
##                                            ##
################################################

# Load modules
import sys
import os
import atexit
import numpy as np
import h5py
#
from PyQt5.QtWidgets import QMessageBox, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog, QMainWindow, QAction, QTabWidget, QTreeWidget, QSizePolicy, QMenu,qApp
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon
#
dirname, filename = os.path.split(os.path.abspath(__file__))
sys.path.append(dirname + '/modules')
sys.path.append(dirname + '/modulesAnalysis')
#
from standardFunctionsGeneral import readNodes, readElements, readSetup
from standardWidgets import sepLine, saveAndExitButton, messageboxOK
#
from model import model
from Controller import Controller
from vtkWindow import vtkWindow
from graphWindow import graphWindow
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
        self.setStyleSheet("background-color: white;")
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        self.setupMenu() # Create the menu
        self.setWindowTitle('InA Analysis Tool')
        #
        self.locPath = os.path.dirname(os.path.abspath(__file__)) # where we are
        self.myFont = QFont("Verdana", 12)
        self.myModel = model() # all model information are saved here
        self.myModel.blockInfo.itemClicked.connect(self.update3D) # table containing model information (click event)
        #
        self.setupGui()
        self.show()
        self.statusBar().showMessage('Ready')

    def about(self):
        """
        Message box with information on the program
        """
        messageboxOK('About', 'Analysis Tool\n' +
                                    'Institute for Acoustics, Braunschweig\n' +
                                    'Version 1.0 (2021)\n\n' +
                                    'Program to view hdf5 result files.\n')

    def loadInput(self):
        """
        Open an hdf5 file (self.loadButton click event)
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","hdf5 file (*.hdf5)", options=options)
        if fileName:
            fileEnding = fileName.split('.')[-1]
            if fileEnding in ['hdf5']:
                # hdf5 file already opened
                if self.myModel.hdf5File: 
                    self.myModel.hdf5File.close()
                    self.myModel.reset()
                self.vtkWindow.clearWindow()
                self.myModel.name = fileName.split('/')[-1].split('.')[0]
                self.myModel.path =  '/'.join(fileName.split('/')[:-1])
                self.myModel.fileEnding = fileName.split('.')[-1]
                success = self.openHdf5()
                # Update 2D / 3D windows
                if success:
                    self.myModel.updateModel(self.vtkWindow)
                self.vtkWindow.currentFrequencyStep = int(len(self.myModel.frequencies)/2.)
                scaleFactor = max( [abs(max(self.myModel.nodes[:]['xCoords'])-min(self.myModel.nodes[:]['xCoords'])), abs(max(self.myModel.nodes[:]['yCoords'])-min(self.myModel.nodes[:]['yCoords'])), abs(max(self.myModel.nodes[:]['zCoords'])-min(self.myModel.nodes[:]['zCoords']))] )
                self.vtkWindow.defineAxisLength(scaleFactor)
                self.graphWindow.currentFrequency = self.myModel.frequencies[ self.vtkWindow.currentFrequencyStep ]
                self.update2D()
                self.update3D()
                # Update tabs
                self.statusBar().showMessage('Model loaded')
            else:
                self.statusBar().showMessage('Unknown file ending (cub5 and hdf5 supported) - no model loaded!')
        
    def openHdf5(self):
        fileName = self.myModel.path + '/' + self.myModel.name + '.hdf5'
        self.myModel.hdf5File = h5py.File(fileName, 'r+')
        atexit.register(self.myModel.hdf5File.close)
        readElements(self.myModel, self.myModel.hdf5File)
        readNodes(self.myModel, self.myModel.hdf5File)
        readSetup(self.myModel, self.myModel.hdf5File)
        messageboxOK('Ready','hdf5 file successfully loaded')
        return 1
        
    def setupGui(self):
        """
        Initialisation of gui (main window content)
        """
        ### Basic splitting in areas ###
        self.mainLayoutLeft = QVBoxLayout()
        self.mainLayoutRight = QVBoxLayout()
        #
        # CREATE WIDGETS | I Left tab container
        self.tabWidget = QTabWidget()
        self.tabWidget.setMovable(True)
        # 1a | Data tree
        self.dataTree = QTreeWidget()
        self.dataTree.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.dataTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.dataTree.setHeaderHidden(1)
        self.dataTree.setStyleSheet("background-color: white;")
        self.tabWidget.addTab(self.dataTree, "Data structure")
        self.tabWidget.setTabIcon(0, QIcon(r'{}\pics\tree.png'.format(os.getcwd())))
        self.tabWidget.setIconSize(QSize(30, 30))
        # ADD TO LAYOUT
        self.mainLayoutLeft.addWidget(self.tabWidget)
        #
        # CREATE WIDGETS | II - 3D Window
        self.vtkWindowParent = QWidget()
        self.vtkWindow = vtkWindow(self.vtkWindowParent, self.locPath)
        self.vtkWindow.setMinimumWidth(450)
        self.vtkWindow.setMinimumHeight(250)
        # ADD TO LAYOUT
        self.mainLayoutRight.addLayout(self.vtkWindow.selectionLayout)
        self.mainLayoutRight.addWidget(self.vtkWindow)
        self.mainLayoutRight.setStretchFactor(self.vtkWindow, True)
        #
        # CREATE WIDGETS | III - 2D Graph
        self.graphWindow = graphWindow()
        #self.graphWindow.setLabels('-','-')
        #self.graphWindow.setMinimumWidth(450)
        #self.graphWindow.setMinimumHeight(250)
        # ADD TO LAYOUT
        self.mainLayoutRight.addWidget(self.graphWindow)
        self.mainLayoutRight.setStretchFactor(self.graphWindow, True)
        #
        ### ADD all sub-layouts TO MAIN LAYOUT
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
        self.menubar.setStyleSheet("QMenuBar::item:selected { background: #abc13b; } QMenu::item:selected { background: #abc13b; }")
        #
        self.fileMenu = self.menubar.addMenu('&File')
        exitAct = QAction('&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.close)
        self.fileMenu.addAction(exitAct)
        #
        self.modelMenu = self.menubar.addMenu('&Model')
        self.loadAct = QAction('&Load model', self)
        self.loadAct.setShortcut('Ctrl+L')
        self.loadAct.setStatusTip('Load model from hdf5 file')
        self.modelMenu.addAction(self.loadAct)
        #
        self.modelMenu = self.menubar.addMenu('&Help')
        helpAct = QAction('&About', self)
        helpAct.setShortcut('Ctrl+H')
        helpAct.setStatusTip('About the program')
        helpAct.triggered.connect(self.about)
        self.modelMenu.addAction(helpAct)
        
    def contextMenuEvent(self, event):
        cmenu = QMenu(self)
        cmenu.setStyleSheet("QMenu::item:selected { background: #abc13b; }")
        #openAct = cmenu.addAction("Open")
        quitAct = cmenu.addAction("Quit")
        action = cmenu.exec_(self.mapToGlobal(event.pos()))

        if action == quitAct:
            qApp.quit()
            
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
    app = QApplication([])
    gui = loadGUI()
    inaController = Controller(gui)
    #
    app.exec_()
    
