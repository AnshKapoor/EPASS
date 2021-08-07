from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QFont
from standardWidgets import loadTypeSelector, addButton, messageboxOK
from loads import loadInfoBox

from planeWave import planeWave
from normVelo import normVelo
#from diffuseField import diffuseField
from timeVarDat import timeVarDat
from tbl import tbl
from pointForce import pointForce

class loadsTab(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.tabLayout = QVBoxLayout(self)
        self.subLayouts = []
        self.changeObjects = []
        self.myFont = QFont("Verdana", 12)
        self.titleText = "Loads"
        #
        self.typeLabel = QLabel('Load Type')
        self.loadSelector = loadTypeSelector()
        self.addLoadButton = addButton()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.typeLabel)
        self.subLayouts[-1].addWidget(self.loadSelector)
        self.subLayouts[-1].addWidget(self.addLoadButton)
        self.subLayouts[-1].addStretch()
        #
        self.loadInfo = loadInfoBox()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].setStretchFactor(self.loadInfo, True)
        self.subLayouts[-1].addWidget(self.loadInfo)
        #
        [self.tabLayout.addLayout(layout) for layout in self.subLayouts]
        
    def addLoad(self, myModel):
        """
        Add the load selected by self.loadSelector (self.addLoadButton click event)
        """
        if myModel.hdf5File:
            if self.loadSelector.currentText() == 'Plane wave':
                myModel.loads.append(planeWave(myModel))
            if self.loadSelector.currentText() == 'Point force':
                myModel.loads.append(pointForce(myModel))
            if self.loadSelector.currentText() == 'Normal velocity':
                myModel.loads.append(normVelo(myModel))
            # if self.loadSelector.currentText() == 'Diffuse field':
                # myModel.loads.append(diffuseField(myModel))
            if self.loadSelector.currentText() == 'Distributed time domain load':
                myModel.loads.append(timeVarDat(myModel))
            if self.loadSelector.currentText() == 'Turbulent Boundary Layer':
                myModel.loads.append(tbl(myModel))
            # Refresh layout
            self.loadInfo.updateLayout(myModel.loads)
            return 1
        else:
            messageboxOK('Addition of load not possible', 'Open a model first!')
            return 0
    
    def removeLoad(self, myModel):
        """
        Remove a load from model (removeButton click event)
        """
        # Layout is cleared
        self.loadInfo.clearLayout()
        loadIDToRemove = self.sender().id
        myModel.loads[loadIDToRemove].clearLayout() # Set widgets to None (remove Button etc)
        myModel.loads[loadIDToRemove] = None # Set the pointer to None
        myModel.loads.pop(loadIDToRemove) # Remove the entry in list
        self.loadInfo.updateLayout(myModel.loads)
        
    def removeAllLoads(self, myModel):
        """
        Remove all loads from model
        """
        # Layout is cleared
        self.loadInfo.clearLayout()
        for n in range(len(myModel.loads)-1,-1,-1):
            myModel.loads[n].drawCheck.setChecked(0)
            myModel.loads[n].clearLayout() # Set widgets to None (remove Button etc)
            myModel.loads[n] = None # Set the pointer to None
            myModel.loads.pop(n) # Remove the entry in list
        self.loadInfo.updateLayout(myModel.loads)
        
    def update(self, myModel):
        self.loadInfo.updateLayout(myModel.loads)
    
    def data2hdf5(self, myModel): 
        try:
            # Write load data to hdf5 file
            if not 'ElemLoads' in myModel.hdf5File.keys():
                myModel.hdf5File.create_group('ElemLoads')
            elemLoadsGroup = myModel.hdf5File['ElemLoads']
            for dataSet in elemLoadsGroup.keys():
                del elemLoadsGroup[dataSet]
            #
            if not 'NodeLoads' in myModel.hdf5File.keys():
                myModel.hdf5File.create_group('NodeLoads')
            nodeLoadsGroup = myModel.hdf5File['NodeLoads']
            for dataSet in nodeLoadsGroup.keys():
                del nodeLoadsGroup[dataSet]
            #
            for load in myModel.loads:
                if load.superType == 'elemLoad':
                    load.data2hdf5(elemLoadsGroup)
                elif load.superType == 'nodeLoad':
                    load.data2hdf5(nodeLoadsGroup)
                else: 
                    pass
            #
            return 1
        except:
            return 0
    