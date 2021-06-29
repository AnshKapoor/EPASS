#
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit, QHBoxLayout
import vtk
import numpy as np
import math
from standardWidgets import removeButton, editButton, setupLoadWindow, messageboxOK, progressWindow, planeSelector
from standardFunctionsGeneral import isPlateType, isFluid3DType
from loads import elemLoad

class normVelo(elemLoad):
    """
    class for 
    """
    def __init__(self, myModel):
        """
        initialise basic load dependent GUI objects
        """
        super(normVelo, self).__init__()
        self.myModel = myModel
        self.removeButton = removeButton()
        self.editButton = editButton()
        self.type = 'vn'
        #
        self.amp = QLineEdit('0.01')
        self.plane = planeSelector()
        self.planeShift = QLineEdit('0.')
        #
        self.label = QLabel('Normal velocity')
        self.ampLabel = QLabel(self.amp.text() + ' m/s')
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.ampLabel, self.drawCheck, self.editButton]]
        #
        self.initSetupWindow()
        self.init3DActor()
        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        #
        self.editButton.clicked.connect(self.showEdit)
        self.showEdit()

    def clearLayout(self):
        """
        Clear all content in planeWave layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))
    
    def getXYdata(self):
        """
        Return x, y data for plotting; for plane wave: constant amplitude
        """
        return self.myModel.frequencies, len(self.myModel.frequencies)*[float(self.amp.text())], 'tab:orange'

    def init3DActor(self):
        """
        initialize vtk objects of this load
        """
        # Get model infos
        arrowSource = vtk.vtkArrowSource()
        # Arrows for load application
        self.arrowDataLoad = vtk.vtkPolyData()
        arrowPointLoad = vtk.vtkPoints()
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        # Glyph for load symbol
        glyphLoad = vtk.vtkGlyph3D()
        glyphLoad.SetScaleModeToScaleByVector()
        glyphLoad.SetSourceConnection(arrowSource.GetOutputPort())
        glyphLoad.SetInputData(self.arrowDataLoad)
        glyphLoad.Update()
        # Mapper for load
        self.arrowMapperLoad = vtk.vtkPolyDataMapper()
        self.arrowMapperLoad.SetInputConnection(glyphLoad.GetOutputPort())
        # Actor for load
        self.arrowActorLoad = vtk.vtkActor()
        self.arrowActorLoad.GetProperty().SetColor(0., 0.6, 1.)
        self.arrowActorLoad.SetMapper(self.arrowMapperLoad)
        #List of Actors for iteration in vtkWindow
        self.actorsList = [self.arrowActorLoad]

    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupLoadWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Amplitude'), self.amp)
        self.setupWindow.layout.addRow(QLabel('Plane'), self.plane)
        self.setupWindow.layout.addRow(QLabel('Shift'), self.planeShift)
        #
        self.blockChecker = []
        for block in self.myModel.elems:
            self.blockChecker.append(QCheckBox())
            if not isFluid3DType(str(block.attrs['ElementType'])):
                self.blockChecker[-1].setEnabled(False)
            subLayout = QHBoxLayout()
            [subLayout.addWidget(wid) for wid in [self.blockChecker[-1], QLabel('Block ' + str(block.attrs['Id']) + ' (' + str(block.attrs['ElementType']) + ')')]]
            subLayout.addStretch()
            self.setupWindow.blockLayout.addLayout(subLayout)
        self.setupWindow.blockLayout.addStretch()
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())
    
    def showEdit(self):
        """
        recalculates data with new input parameters
        """
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            pass
        elif var == 1: # set new values
            try:
                self.ampLabel.setText(str(float(self.amp.text())) + ' m/s')
                self.findRelevantFaces(self.plane.currentText(), float(self.planeShift.text()))
                self.update3DActor()
                self.switch()
            except: # if input is wrong, show message and reset values
                messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                #self.resetValues()
        else:
            pass
            #self.resetValues()
        return var

    def update3DActor(self):
        """
        updates the vtk actors
        """
        # Get model infos
        nodes = self.myModel.nodes
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
        # Update load
        arrowPointLoad = vtk.vtkPoints()
        # get a lower number of arrows if there are more elements or the element size is small
        try: 
            arrNoScale = int(len(self.surfacePoints)/100.) # draw every 100th arrow in case there are >100 arrows
            if arrNoScale<1:
                arrNoScale = 1
        except: 
            arrNoScale = 1
        [arrowPointLoad.InsertNextPoint([self.surfacePoints[p][0] + 0.3*scaleFactor*self.surfaceFacesNormals[p][0], self.surfacePoints[p][1] + 0.3*scaleFactor*self.surfaceFacesNormals[p][1], self.surfacePoints[p][2] + 0.3*scaleFactor*self.surfaceFacesNormals[p][2]]) for p in range(0,len(self.surfacePoints),arrNoScale)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3) 
        [arrowVectorsLoad.InsertNextTuple([-0.3*scaleFactor*self.surfaceFacesNormals[p][0], -0.3*scaleFactor*self.surfaceFacesNormals[p][1], -0.3*scaleFactor*self.surfaceFacesNormals[p][2]]) for p in range(0,len(self.surfacePoints),arrNoScale)]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()
        nodes = 0
    
        