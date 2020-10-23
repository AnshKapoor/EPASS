import sys
import os
from PyQt5.QtWidgets import QApplication, QPushButton, QMainWindow,QButtonGroup
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
###############################IMPORTING MATERIAL CLASSES###########################
sys.path.append('./tabs/materials')
from Structural_Isotropic_dev import Structural_Isotropic
from Structural_Orthotropic_dev import Structural_Orthotropic
from Structural_viscoOrthotropic_dev import Structural_viscoOrthotropic
from Fluid_dev import Fluid
from Viscoelastic_dev import Viscoelastic
from ViscoelasticCLD_CH_dev import ViscoelasticCLD_CH
from ViscoelasticCLD_RKU_dev import ViscoelasticCLD_RKU
from Fluid_loss_dev import Fluid_loss
from equiv_Fluid_dev import equivfluid
from Cloaking_fluid_dev import Cloaking_fluid
from Poro_Elastic_dev import Poro_Elastic
from Frequency_Viscoelastic_dev import Frequency_Viscoelastic
from Frequency_Viscoelastic_Param_dev import Frequency_Viscoelastic_Param
from spring_dev import spring
from pointmass_dev import pointmass

###############################IMPORTING MATERIAL CLASSES###########################
class trial_mat(QtWidgets.QMainWindow):
    def __init__(self):
        super(trial_mat, self).__init__()
        #self.setGeometry(20,20,600,400)
        #self.setWindowTitle("Material Tab")

        # Define all supported types
        self.mat_types = ['AAAIsotropic', 'Orthotropic', 'viscoorthotropic', 'Fluid', 'Viscoelastic', 'CLD:Cremer/Heckl',
        'CLD:Ross/Kerwin/Ungar', 'Fluidloss', 'EquivalentFluidDirect', 'Cloaking', 'Poro3d',
        'Viscofreq', 'Viscofreqparam', 'Spring','Pointmass']  # list must be updated when new materials are added
        self.test="JauJauTestString"
        # Initialize layout and arrays
        self.main_layout = QGridLayout()
        self.horiz_layout = QHBoxLayout()
        self.vert_layout= QVBoxLayout()
        self.Mat_Object = []  # stores references to all material objects
        self.Mat_Para = []  # stores references to all material data corresponding to Mat_Object
        self.MatCheckBox = []  # stores checkboxes corresponding to BC_Object
        self.deleteBox =[] #Stores all the delete buttons
        self.btn_grp = QButtonGroup() #Used to give id to all delete buttons

        # Create scrollcontainer widget with respective scroll layout area
        self.scrollcontainer = QWidget()
        self.scrollcontainer.horiz_layout = QGridLayout(self.scrollcontainer)





        self.basic()

    #basic appearence of the tab
    def basic(self):
        ############## Initializing with two material types###################################
        self.addMatToTabData(Structural_Isotropic('Steel', 1, 210000000000, 0.3, 0, 0, 0, 0, 0, 7850, 0, 0))
        self.addMatToTabData(Structural_Isotropic('Aluminium', 2, 70000000000, 0.34, 0, 0, 0, 0, 0, 2700, 0, 0))

        ############## Creating initial layouts and buttons ###################################3

        mat_label = QLabel()
        mat_label.setText("Add Material of Type:")
        mat_label.setMaximumWidth(110)

        # Create dropdown
        self.comboBox = QComboBox(self)
        self.comboBox.setMaximumWidth(100)
        self.comboBox.addItems(self.mat_types)

        #Add material Button
        addMat = QPushButton('', self)  # construct add-button
        addMat.setMaximumWidth(25)
        addMat.setIcon(QtGui.QIcon('./tabs/add_button.png'))
        addMat.setIconSize(QtCore.QSize(15, 15))  # set size of button image
        addMat.setToolTip('<b>Add the selected material type.</b>')
        addMat.clicked.connect(self.addRow) # set functionality when clicked

        # Save Mat Button
        saveMat = QPushButton('Save internally and to file', self)  # construct load-button
        saveMat.setMaximumWidth(150)
        saveMat.setToolTip('<b>Save your mat file and substitue all materials. (Attention: Overwrites existing file!!!)</b>')
        #saveMat.clicked.connect(self.saveMatToFile)
        saveMat.clicked.connect(self.prepareForExport)

        # Setting Layouts for all the widgets
        self.horiz_layout.setSpacing(15)
        self.horiz_layout.addWidget(mat_label)
        self.horiz_layout.addWidget(self.comboBox)
        self.horiz_layout.addWidget(addMat)
        self.horiz_layout.addWidget(saveMat)
        self.main_layout.addLayout(self.horiz_layout,0,0,Qt.AlignTop)
        widget = QWidget()
        widget.setLayout(self.main_layout)
        self.setCentralWidget(widget)


        self.show_mat() # to display materials added
        self.show()



    def show_mat(self):
        self.scrollcontainer = QWidget()
        self.scrollcontainer.horiz_layout = QGridLayout(self.scrollcontainer)
        self.btn_grp = QButtonGroup() # to reinitialize and over write the QButtonGroup
        self.deleteBox = []
        self.scroll = QScrollArea() # to overwrite the scroll area

        ### Delete all layout content, if existing
        for lay in [ self.scrollcontainer.horiz_layout ]:
            for i in reversed(range(lay.count())):
                if isinstance(lay.itemAt(i), QtWidgets.QWidgetItem):
                    lay.takeAt(i).widget().setParent(None)
                else:
                    lay.removeItem(lay.takeAt(i))

        # Creating delete buttons and grouping them
        for i in range(len(self.Mat_Object)):

            newdelButton = QtWidgets.QPushButton('')  # construct Close-Button
            newdelButton.setIconSize(QtCore.QSize(15, 15))  # Set size of button image
            newdelButton.setIcon(QtGui.QIcon('./tabs/del_button.png'))
            newdelButton.setToolTip('<b>Delete Material</b>')  #
            # self.delButton.setIcon(QtGui.QIcon(os.path.dirname(os.path.abspath(__file__))+'/../../../pics/del_button.png'))

            self.btn_grp.addButton(newdelButton)
            self.btn_grp.setId(newdelButton,i)
            self.deleteBox.append(newdelButton)


            for j in range(0, self.Mat_Object[i].length):

                self.scrollcontainer.horiz_layout.addWidget(self.Mat_Para[i][j], 2 * i + 1, 2 * j + 3, 1,1)
                self.scrollcontainer.horiz_layout.addWidget( self.deleteBox[i], 2 * i + 1, 2, 1, 1)

        self.btn_grp.buttonClicked.connect(self.deleteRow, self.btn_grp.checkedId()) # sends id to deleteRow on being clicked to delete material
        # setting scroll layout
        self.scroll.setWidget(self.scrollcontainer)
        self.scroll.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll, 1, 0, 1, Qt.Alignment())

        # deletes the selected row
    def deleteRow(self, delbuttonnum):

          objNo= self.btn_grp.id( delbuttonnum)
          del self.Mat_Object[objNo]
          del self.Mat_Para[objNo]
          self.show_mat()

    def addRow(self):
        matType = self.comboBox.currentText()

        newId = self.get_freeID()
        if matType == 'Isotropic':
            self.addMatToTabData(Structural_Isotropic('New_Struct', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Viscoelastic':
            self.addMatToTabData(Viscoelastic('New_viscoelastic', newId, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Viscofreq':
            self.addMatToTabData(Frequency_Viscoelastic('New_frequency-viscoelastic', newId, 0, 0, 0, 0, 0, 0))

        if matType == 'Viscofreqparam':
            self.addMatToTabData(Frequency_Viscoelastic_Param('New_freq-visco-param', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Orthotropic':
            self.addMatToTabData(Structural_Orthotropic('New_Struct', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'viscoorthotropic':
            self.addMatToTabData(Structural_viscoOrthotropic('New_Struct', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'CLD:Cremer/Heckl':
            self.addMatToTabData(ViscoelasticCLD_CH('New_CLD_CH', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'CLD:Ross/Kerwin/Ungar':
            self.addMatToTabData(ViscoelasticCLD_RKU('New_CLD_RKU', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Fluid':
            self.addMatToTabData(Fluid('New_Fluid', newId, 0, 0, 0))

        if matType == 'Fluidloss':
            self.addMatToTabData(Fluid_loss('New_Fluid_with_loss', newId, 0, 0, 0, 0, 0))

        if matType == 'EquivalentFluidDirect':
            self.addMatToTabData(equivfluid('New_equivalent_Fluid', newId, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Cloaking':
            self.addMatToTabData(Cloaking_fluid('New_Cloaking_fluid', newId, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Poro3d':
            self.addMatToTabData(Poro_Elastic('New_Poro_Elastic', newId, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

        if matType == 'Spring':
            self.addMatToTabData(spring('New_spring', newId, 0, 0, 0, 0, 0, 0, 1, 0))

        if matType == 'Pointmass':
            self.addMatToTabData(pointmass('New_pointmass', newId, 0))
        self.show_mat()

    def get_freeID(self):
        Idlist = []
        if not self.Mat_Object: # When no material is defined
            return '1'
        for obj in self.Mat_Object:
            Idlist += [str(obj.Id.text())]
        for n in range(1, len(Idlist)+1):
            if str(n) not in Idlist:
                return str(n)
        return str(len(Idlist)+1)

    def addMatToTabData(self, NewMaterialObject):
        self.Mat_Object.append(NewMaterialObject)
        self.Mat_Para.append(NewMaterialObject.getInfo())


    def prepareForExport(self):
        self.MatList = []
        for iMat, Mat in enumerate(self.Mat_Object):
            if (isinstance(Mat, Structural_Isotropic) or isinstance(Mat, Viscoelastic) or isinstance(Mat,
                                                                                                     Frequency_Viscoelastic) or Frequency_Viscoelastic_Param or
                    isinstance(Mat, Structural_Orthotropic) or isinstance(Mat,
                                                                          Structural_viscoOrthotropic) or isinstance(
                        Mat, ViscoelasticCLD_CH) or isinstance(Mat, ViscoelasticCLD_RKU) or
                    isinstance(Mat, Fluid) or isinstance(Mat, Fluid_loss) or isinstance(Mat,
                                                                                        equivfluid) or isinstance(
                        Mat, Cloaking_fluid) or
                    isinstance(Mat, Poro_Elastic) or isinstance(Mat, spring) or isinstance(Mat, pointmass)):


                self.MatList.append(Mat.getExportData())



    def saveMatToFile(self):

            with open('SavedMaterials.txt', 'w') as f:
                for iMat, Mat in enumerate(self.Mat_Object):
                    if (isinstance(Mat, Structural_Isotropic) or isinstance(Mat, Viscoelastic) or isinstance(Mat,
                                                                                                             Frequency_Viscoelastic) or Frequency_Viscoelastic_Param or
                            isinstance(Mat, Structural_Orthotropic) or isinstance(Mat,
                                                                                  Structural_viscoOrthotropic) or isinstance(
                                Mat, ViscoelasticCLD_CH) or isinstance(Mat, ViscoelasticCLD_RKU) or
                            isinstance(Mat, Fluid) or isinstance(Mat, Fluid_loss) or isinstance(Mat,
                                                                                                equivfluid) or isinstance(
                                Mat, Cloaking_fluid) or
                            isinstance(Mat, Poro_Elastic) or isinstance(Mat, spring) or isinstance(Mat, pointmass)):
                        f.write(' '.join(Mat.getExportData()) + '\n')

                print
                ('Saving file succesful!')

    def tester(self):
        print('Jau, das haut hin!')

# def run():
#     app = QApplication([])
#     GUI = trial_mat()
#     trial_mat.basic(GUI)
#     sys.exit(app.exec_())



#run()
