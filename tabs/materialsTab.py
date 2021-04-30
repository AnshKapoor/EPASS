import sys
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QFont
from standardWidgets import addButton, messageboxOK, materialTypeSelector
###############################IMPORTING MATERIAL CLASSES###########################
sys.path.append('./materials')
from materials import matInfoBox
# Single materials
from STR_LIN_ELA_ISO_DIR import STR_LIN_ELA_ISO_DIR
from AF_LIN_UAF_ISO_DIR import AF_LIN_UAF_ISO_DIR
from STR_LIN_VIS_ISO_DIR import STR_LIN_VIS_ISO_DIR
# Acoustic linear materials

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
        self.subLayouts.append(QHBoxLayout())
        self.subLayouts[-1].addWidget(self.typeLabel)
        self.subLayouts[-1].addWidget(self.materialSelector)
        self.subLayouts[-1].addWidget(self.addMaterialButton)
        self.subLayouts[-1].addStretch()
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
            if self.materialSelector.currentText() == 'STR_LIN_ELA_ISO_DIR':
                myModel.materials.append(STR_LIN_ELA_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'AF_LIN_UAF_ISO_DIR':
                myModel.materials.append(AF_LIN_UAF_ISO_DIR(self.getFreeId(myModel.materials)))
            if self.materialSelector.currentText() == 'STR_LIN_VIS_ISO_DIR':
                myModel.materials.append(STR_LIN_VIS_ISO_DIR(self.getFreeId(myModel.materials)))
            # if self.materialSelector.currentText() == '?':
                # myModel.materials.append(?)
            # ...
            # Refresh layout
            self.matInfo.updateLayout(myModel.materials)
            return 1
        else:
            messageboxOK('Addition of load not possible', 'Open a model first!')
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
            [material.data2hdf5(materialsGroup) for material in myModel.materials]
            #
            return 1
        except:
            return 0
    