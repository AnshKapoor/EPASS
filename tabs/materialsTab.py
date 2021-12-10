import sys, os
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout, QFileDialog, QTableWidgetItem
from PyQt5.QtGui import QFont
from standardWidgets import addButton, messageboxOK, materialTypeSelector
###############################IMPORTING MATERIAL CLASSES###########################
sys.path.append('./materials')
from materials import matInfoBox
import numpy as np
# Structural linear materials
from STR_LIN_ELA_ISO_DIR import STR_LIN_ELA_ISO_DIR
from STR_LIN_VIS_ISO_DIR import STR_LIN_VIS_ISO_DIR
from STR_LIN_VIS_ORT_DIR import STR_LIN_VIS_ORT_DIR
from STR_LIN_VIS_ORT_LAM import STR_LIN_VIS_ORT_LAM
from STR_LIN_MAS_ISO_DIR import STR_LIN_MAS_ISO_DIR
from STR_LIN_SPR_ORT_DIR import STR_LIN_SPR_ORT_DIR
# Acoustic linear materials
from AF_LIN_UAF_ISO_DIR import AF_LIN_UAF_ISO_DIR
from AF_LIN_DAF_ISO_DIR import AF_LIN_DAF_ISO_DIR
from AF_LIN_EQF_ISO_DIR import AF_LIN_EQF_ISO_DIR

# from Structural_Orthotropic_dev import Structural_Orthotropic
# from Structural_viscoOrthotropic_dev import Structural_viscoOrthotropic
# from Fluid_dev import Fluid
# from Viscoelastic_dev import Viscoelastic
# from ViscoelasticCLD_CH_dev import ViscoelasticCLD_CH
# from ViscoelasticCLD_RKU_dev import ViscoelasticCLD_RKU
# from Fluid_loss_dev import Fluid_loss
# from equiv_Fluid_dev import equivfluid
# from Cloaking_fluid_dev import Cloaking_fluid
# from Poro_Elastic_dev import Poro_Elastic
# from Frequency_Viscoelastic_dev import Frequency_Viscoelastic
# from Frequency_Viscoelastic_Param_dev import Frequency_Viscoelastic_Param
# from spring_dev import spring
# from pointmass_dev import pointmass

class materialsTab(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.tabLayout = QVBoxLayout(self)
        self.subLayouts = []
        self.changeObjects = []
        self.myFont = QFont("Verdana", 12)
        self.titleText = "Materials"
        #
        self.typeLabel = QLabel('Material Type')
        self.materialSelector = materialTypeSelector()
        self.addMaterialButton = addButton()
        self.importMaterialButton = addButton()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.typeLabel)
        self.subLayouts[-1].addWidget(self.materialSelector)
        self.subLayouts[-1].addWidget(self.addMaterialButton)
        self.subLayouts[-1].addStretch()
        self.subLayouts[-1].addWidget(QLabel('Import materials'))
        self.subLayouts[-1].addWidget(self.importMaterialButton)
        #
        self.matInfo = matInfoBox()
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].setStretchFactor(self.matInfo, True)
        self.subLayouts[-1].addWidget(self.matInfo)
        #
        [self.tabLayout.addLayout(layout) for layout in self.subLayouts]
        
    def addMaterial(self, myModel):
        """
        Add the material selected by self.matSelector (self.addMaterialButton click event)
        """
        if myModel.hdf5File:
            if self.materialSelector.currentText() == 'STRUCT linear elastic iso': 
                myModel.materials.append(STR_LIN_ELA_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'STRUCT linear visco iso':
                myModel.materials.append(STR_LIN_VIS_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'STRUCT linear visco ort':
                myModel.materials.append(STR_LIN_VIS_ORT_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'STRUCT linear visco ort pre':
                myModel.materials.append(STR_LIN_VIS_ORT_LAM(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'STRUCT linear pointmass':
                myModel.materials.append(STR_LIN_MAS_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'STRUCT linear spring':
                myModel.materials.append(STR_LIN_SPR_ORT_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'ACOUS undamped fluid iso':
                myModel.materials.append(AF_LIN_UAF_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'ACOUS damped fluid iso':
                myModel.materials.append(AF_LIN_DAF_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'ACOUS equivalent fluid iso':
                myModel.materials.append(AF_LIN_EQF_ISO_DIR(self.getFreeId(myModel.materials)))
            # if self.materialSelector.currentText() == '?':
                # myModel.materials.append(?)
            # ...
            # Refresh layout
            self.matInfo.updateLayout(myModel.materials)
            return 1
        else:
            messageboxOK('Addition of material not possible', 'Open a model first!')
            return 0
    
    def importMaterial(self, myModel):
        """
        Imports materials from ascii file
        """
        if myModel.hdf5File:
            messageboxOK('File required', 'Please select an ascii file containing the material data.<br><br>File format: One blankspace-separated line per material<br>Material type in the first column followed by id and the parameter values.')
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","ascii file (*.dat *.txt)", options=options)
            if fileName:
                f = open(fileName, 'r')
                for line in f:
                    myData = line.split()
                    if myData[0] == 'STR_LIN_ELA_ISO_DIR':
                        newMat = STR_LIN_ELA_ISO_DIR(myData[1])
                    elif myData[0] == 'STR_LIN_VIS_ISO_DIR':
                        newMat = STR_LIN_VIS_ISO_DIR(myData[1])
                    elif myData[0] == 'STR_LIN_VIS_ORT_DIR':
                        newMat = STR_LIN_VIS_ORT_DIR(myData[1])
                    elif myData[0] == 'STR_LIN_VIS_ORT_LAM':
                        newMat = STR_LIN_VIS_ORT_LAM(myData[1])
                    elif myData[0] == 'STR_LIN_MAS_ISO_DIR':
                        newMat = STR_LIN_MAS_ISO_DIR(myData[1])
                    elif myData[0] == 'STR_LIN_SPR_ORT_DIR':
                        newMat = STR_LIN_SPR_ORT_DIR(myData[1])
                    elif myData[0] == 'AF_LIN_UAF_ISO_DIR':
                        newMat = AF_LIN_UAF_ISO_DIR(myData[1])
                    elif myData[0] == 'AF_LIN_DAF_ISO_DIR':
                        newMat = AF_LIN_DAF_ISO_DIR(myData[1])
                    elif myData[0] == 'AF_LIN_EQF_ISO_DIR':
                        newMat = AF_LIN_EQF_ISO_DIR(myData[1])
                    else:
                        newMat = STR_LIN_ELA_ISO_DIR(0)
                        myData = []
                    if len(myData) == len(newMat.parameterNames)+3:
                        newMat.name.setText(myData[2])
                        for n, entry in enumerate(myData[3:]): 
                            try: # Check if number
                                float(entry)
                                newMat.parameterValues[n].setText(entry)
                            except: # else search for given string as filename
                                requestedFdependentFileName = os.path.split(fileName)[0] + '\\' + entry
                                if os.path.isfile(requestedFdependentFileName) and newMat.allowFrequencyDependentValues[n]: 
                                    f = open(requestedFdependentFileName, 'r')
                                    table = newMat.frequencyDependentEdits[n].table 
                                    maxRows = table.rowCount()
                                    lineCounter = 0
                                    for line in f:
                                        if lineCounter > maxRows-1: 
                                            table.insertRow(table.rowCount())
                                        table.setItem(lineCounter, 0, QTableWidgetItem(line.split()[0]))
                                        table.setItem(lineCounter, 1, QTableWidgetItem(line.split()[1]))
                                        lineCounter = lineCounter + 1
                                    newMat.parameterValues[n].setText('freq-dependent')
                                    newMat.parameterValues[n].setEnabled(False)
                        myModel.materials.append(newMat)
            else:
                return 0
            # Refresh layout
            self.matInfo.updateLayout(myModel.materials)
            return 1
        else:
            messageboxOK('Addition of material not possible', 'Open a model first!')
            return 0
            
    def removeMaterial(self, loadIDToRemove, myModel):
        """
        Remove a material from model (removeButton click event)
        """
        # Layout is cleared
        self.matInfo.clearLayout()
        if loadIDToRemove=='button':
            loadIDToRemove = self.sender().id
        myModel.materials[loadIDToRemove].clearLayout() # Set widgets to None (remove Button etc)
        myModel.materials[loadIDToRemove] = None # Set the pointer to None
        myModel.materials.pop(loadIDToRemove) # Remove the entry in list
        self.matInfo.updateLayout(myModel.materials)
        
    def getFreeId(self, materials):
        Idlist = []
        if not materials: # When no material is defined
            return '1'
        for mat in materials:
            Idlist += [str(mat.Id.text())]
        for n in range(1, len(Idlist)+1):
            if str(n) not in Idlist:
                return str(n)
        return str(len(Idlist)+1)
        
    def removeAllMaterials(self, myModel):
        """
        Remove all materials from model
        """
        # Layout is cleared
        self.matInfo.clearLayout()
        for n in range(len(myModel.materials)-1,-1,-1):
            myModel.materials[n].clearLayout() # Set widgets to None (remove Button etc)
            myModel.materials[n] = None # Set the pointer to None
            myModel.materials.pop(n) # Remove the entry in list
        self.matInfo.updateLayout(myModel.materials)
        
    def update(self, myModel):
        self.matInfo.updateLayout(myModel.materials)
    
    def data2hdf5(self, myModel): 
        try:
            # Write material data to hdf5 file
            if not 'Materials' in myModel.hdf5File.keys():
                myModel.hdf5File.create_group('Materials')
            materialsGroup = myModel.hdf5File['Materials']
            #
            for dataSet in materialsGroup.keys():
                del materialsGroup[dataSet]
            #
            # Write f-dependent material data to hdf5 file
            if not 'Parameters' in myModel.hdf5File.keys():
                myModel.hdf5File.create_group('Parameters')
            parametersGroup = myModel.hdf5File['Parameters']
            #
            for dataSet in parametersGroup.keys():
                del parametersGroup[dataSet]
            #
            materialsGroup.attrs['N'] = np.int64(len(myModel.materials))
            [material.data2hdf5(materialsGroup,parametersGroup) for material in myModel.materials]
            #
            return 1
        except:
            return 0
    