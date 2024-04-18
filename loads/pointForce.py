#
from PyQt5.QtWidgets import QLabel, QWidgetItem, QCheckBox, QLineEdit
import vtk
from standardWidgets import removeButton, editButton, setupNodeLoadWindow, messageboxOK
from loads import nodeLoad

class pointForce(nodeLoad):
    """
    class for plane wave loads. provides methods to calculate pressure/phases acc. to load vector
    """
    def __init__(self, myModel):
        """
        initialise basic load dependent GUI objects
        """
        super(pointForce, self).__init__()
        self.myModel = myModel
        self.removeButton = removeButton()
        self.editButton = editButton()
        self.type = 'point_force'
        #
        self.dirX = QLineEdit('1.')
        self.dirY = QLineEdit('1.')
        self.dirZ = QLineEdit('1.')
        self.amp = (float(self.dirX.text())**2 + float(self.dirY.text())**2 + float(self.dirZ.text())**2)**0.5
        #
        self.label = QLabel('Point force')
        self.ampLabel = QLabel(str(self.amp) + ' N')
        self.dirLabel = QLabel('x ' + self.dirX.text() + ' y ' + self.dirY.text() + ' z ' + self.dirZ.text())
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.ampLabel, self.dirLabel, self.drawCheck, self.editButton]]
        #
        self.initSetupWindow()
        self.init3DActor()
        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        #
        self.editButton.clicked.connect(self.showEdit)
        var = self.showEdit()
        if var == 0: # is the case if the initial setup window is canceled by the user
            self.update3DActor()

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
        Return x, y data for plotting; for point force: constant amplitude
        """
        return self.myModel.frequencies, len(self.myModel.frequencies)*[float(self.amp)], 'tab:green'

    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupNodeLoadWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Force in X'), self.dirX)
        self.setupWindow.layout.addRow(QLabel('Force in Y'), self.dirY)
        self.setupWindow.layout.addRow(QLabel('Force in Z'), self.dirZ)
        #
        self.nodesetChecker = []
        for nodeSet in self.myModel.nodeSets:
            self.nodesetChecker.append(QCheckBox())
            self.setupWindow.nodesetLayout.addRow(self.nodesetChecker[-1], QLabel('Nodeset ' + str(nodeSet.attrs['Id'])))
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())

    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate([self.dirX, self.dirY, self.dirZ]):
            item.setText(self.varSave[n])

    def showEdit(self):
        """
        recalculates data with new input parameters
        """
        self.varSave = [self.dirX.text(), self.dirY.text(), self.dirZ.text()]
        var = self.setupWindow.exec()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                if float(self.dirX.text()) == 0. and float(self.dirY.text()) == 0. and float(self.dirZ.text()) == 0.:
                    raise Exception
                self.dirLabel.setText('x ' + str(float(self.dirX.text())) + ' y ' + str(float(self.dirY.text())) + ' z ' + str(float(self.dirZ.text())))
                self.amp = (float(self.dirX.text())**2 + float(self.dirY.text())**2 + float(self.dirZ.text())**2)**0.5
                self.ampLabel.setText(str(self.amp) + ' N')
                # Extract nodes of selected nodesets
                self.findRelevantPoints()
                self.update3DActor()
                self.switch()
            except: # if input is wrong, show message and reset values
                messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                self.resetValues()
        else:
            self.resetValues()
        return var

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
        self.arrowActorLoad.GetProperty().SetColor(0., 1., 0.6)
        self.arrowActorLoad.SetMapper(self.arrowMapperLoad)
        #List of Actors for iteration in vtkWindow
        self.actorsList = [self.arrowActorLoad]

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
            arrNoScale = int(len(self.nodePoints)/100.) # draw every 100th arrow in case there are >100 arrows
            if arrNoScale<1:
                arrNoScale = 1
        except: 
            arrNoScale = 1
        [arrowPointLoad.InsertNextPoint([self.nodePoints[p,0] + 0.3*scaleFactor*float(self.dirX.text())/self.amp, self.nodePoints[p,1] + 0.3*scaleFactor*float(self.dirY.text())/self.amp, self.nodePoints[p,2] + 0.3*scaleFactor*float(self.dirZ.text())/self.amp]) for p in range(0,len(self.nodePoints),arrNoScale)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.3*scaleFactor*float(self.dirX.text())/self.amp, -0.3*scaleFactor*float(self.dirY.text())/self.amp, -0.3*scaleFactor*float(self.dirZ.text())/self.amp]) for p in range(0,len(self.nodePoints),arrNoScale)]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()
        nodes = 0
    
    def processArguments(self, load_args):
        self.dirX.setText(str(load_args[0][0]))
        self.dirY.setText(str(load_args[0][1]))
        self.dirZ.setText(str(load_args[0][2]))

        for row_id, everyCheckBox in enumerate(self.nodesetChecker):
            id = int(self.setupWindow.nodesetLayout.itemAt(row_id*2+1).widget().text().split()[1])
            if id == load_args[1]:
                self.setupWindow.nodesetLayout.itemAt(row_id*2+0).widget().setChecked(True)
        self.showEdit()
