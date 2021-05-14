#
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit, QHBoxLayout
import vtk
import numpy as np
import math
from standardWidgets import removeButton, editButton, setupLoadWindow, messageboxOK, progressWindow
from standardFunctionsGeneral import isPlateType
from loads import elemLoad

class planeWave(elemLoad):
    """
    class for plane wave loads. provides methods to calculate pressure/phases acc. to load vector
    """
    def __init__(self, myModel):
        """
        initialise basic load dependent GUI objects
        """
        super(planeWave, self).__init__()
        self.myModel = myModel
        self.removeButton = removeButton()
        self.editButton = editButton()
        self.type = 'plane_wave'
        #
        self.amp = QLineEdit('1.')
        self.dirX = QLineEdit('1.')
        self.dirY = QLineEdit('1.')
        self.dirZ = QLineEdit('1.')
        self.c = QLineEdit('340.')
        #
        self.label = QLabel('Plane wave')
        self.ampLabel = QLabel(self.amp.text() + ' Pa')
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
            self.generatePressure()
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

    def generatePressure(self):
        """
        Calculates pressure excitation on the selected blocks due to the created plane wave
        """
        c = float(self.c.text())
        frequencies = self.myModel.frequencies
        self.findRelevantPoints()
        if self.surfacePoints is not []:
            self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
            r_vector = []
             # Get model infos
            nodes = self.myModel.nodes
            center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
            loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
            loadNormal = loadNormal/np.linalg.norm(loadNormal)
            # calculate distances in direction of the plane wave
            progWin = progressWindow(len(self.surfacePoints)-1, "Calculating distances")
            for nsp, surfacePoint in enumerate(self.surfacePoints):
                r_vector.append(abs(loadNormal[0]*(surfacePoint[0] - center[0]) + loadNormal[1]*(surfacePoint[1] - center[1]) + loadNormal[2]*(surfacePoint[2] - center[2])))
                progWin.setValue(nsp)
                QApplication.processEvents()
            # calculate the correct phases for the distances and apply the amp requested by the user in loadNormal direction to each element
            progWin = progressWindow(len(frequencies)-1, "Calculating phases")
            for nf, f in enumerate(frequencies):
                lam = c/f # wave length
                self.surfacePhases[nf,:] = [2*math.pi*(r % lam)/lam for r in r_vector]
                progWin.setValue(nf)
                QApplication.processEvents()

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
        nodes = self.myModel.nodes
        center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
        # Symbol for plane wave
        # Calculate random directions in the plane
        direction1 = np.cross(loadNormal, [loadNormal[0]+0.11*loadNormal[1], loadNormal[1]+0.22*loadNormal[2], loadNormal[2]+0.33*loadNormal[0]])
        direction1 = direction1/np.linalg.norm(direction1)
        direction2 = np.cross(loadNormal, direction1)
        direction2 = direction2/np.linalg.norm(direction2)
        # Create vtk quad object
        self.loadGridSymbol = vtk.vtkUnstructuredGrid()
        vtkPoints = vtk.vtkPoints()
        [vtkPoints.InsertNextPoint(center[0] + scaleFactor*loadNormal[0] + scaleFactor*0.2*edge[0], center[1] + scaleFactor*loadNormal[1] + scaleFactor*0.2*edge[1], center[2] + scaleFactor*loadNormal[2] + scaleFactor*0.2*edge[2]) for edge in [-direction1-direction2, -direction1+direction2, direction1+direction2, direction1-direction2]]
        self.loadGridSymbol.SetPoints(vtkPoints)
        quad_ = vtk.vtkQuad()
        [quad_.GetPointIds().SetId(p, p) for p in range(4)] # Set four nodes
        self.loadGridSymbol.InsertNextCell(quad_.GetCellType(), quad_.GetPointIds())
        # Create mapper and actor
        self.loadMapperSymbol = vtk.vtkDataSetMapper()
        self.loadMapperSymbol.SetInputData(self.loadGridSymbol)
        self.loadActorSymbol = vtk.vtkActor()
        self.loadActorSymbol.SetMapper(self.loadMapperSymbol)
        self.loadActorSymbol.GetProperty().SetColor(1., 0.6, 0.)
        self.loadActorSymbol.GetProperty().SetAmbient(0.9);
        self.loadActorSymbol.GetProperty().SetDiffuse(0.1);
        self.loadActorSymbol.GetProperty().SetSpecular(0.);
        # Arrow for direction of load
        self.arrowDataSymbol = vtk.vtkPolyData()
        arrowPointsSymbol = vtk.vtkPoints()
        arrowPointsSymbol.InsertNextPoint(center[0] + scaleFactor*loadNormal[0], center[1] + scaleFactor*loadNormal[1], center[2] + scaleFactor*loadNormal[2])
        self.arrowDataSymbol.SetPoints(arrowPointsSymbol)
        self.arrowVectorsSymbol = vtk.vtkDoubleArray()
        self.arrowVectorsSymbol.SetNumberOfComponents(3)
        self.arrowVectorsSymbol.InsertNextTuple([scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
        self.arrowDataSymbol.GetPointData().SetVectors(self.arrowVectorsSymbol)
        arrowSource = vtk.vtkArrowSource()
        # Glyph for load symbol
        glyphSymbol = vtk.vtkGlyph3D()
        glyphSymbol.SetScaleModeToScaleByVector()
        glyphSymbol.SetSourceConnection(arrowSource.GetOutputPort())
        glyphSymbol.SetInputData(self.arrowDataSymbol)
        glyphSymbol.Update()
        # Mapper for load symbol
        self.arrowMapperSymbol = vtk.vtkPolyDataMapper()
        self.arrowMapperSymbol.SetInputConnection(glyphSymbol.GetOutputPort())
        # Actor for load symbol
        self.arrowActorSymbol = vtk.vtkActor()
        self.arrowActorSymbol.GetProperty().SetColor(1., 0.6, 0.)
        self.arrowActorSymbol.SetMapper(self.arrowMapperSymbol)
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
        self.arrowActorLoad.GetProperty().SetColor(1., 0.6, 0.)
        self.arrowActorLoad.SetMapper(self.arrowMapperLoad)
        #List of Actors for iteration in vtkWindow
        self.actorsList = [self.arrowActorLoad, self.arrowActorSymbol, self.loadActorSymbol]

    def initSetupWindow(self):
        """
        initialisation of setup popup window for parameter/file path input
        """
        self.setupWindow = setupLoadWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Amplitude'), self.amp)
        self.setupWindow.layout.addRow(QLabel('Direction X'), self.dirX)
        self.setupWindow.layout.addRow(QLabel('Direction Y'), self.dirY)
        self.setupWindow.layout.addRow(QLabel('Direction Z'), self.dirZ)
        self.setupWindow.layout.addRow(QLabel('Speed of Sound'), self.c)
        #
        self.blockChecker = []
        for block in self.myModel.elems:
            self.blockChecker.append(QCheckBox())
            if not isPlateType(str(block.attrs['ElementType'])):
                self.blockChecker[-1].setEnabled(False)
            subLayout = QHBoxLayout()
            [subLayout.addWidget(wid) for wid in [self.blockChecker[-1], QLabel('Block ' + str(block.attrs['Id']) + ' (' + str(block.attrs['ElementType']) + ')')]]
            subLayout.addStretch()
            self.setupWindow.blockLayout.addLayout(subLayout)
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())

    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate([self.amp, self.dirX, self.dirY, self.dirZ, self.c]):
            item.setText(self.varSave[n])

    def showEdit(self):
        """
        recalculates data with new input parameters
        """
        self.varSave = [self.amp.text(), self.dirX.text(), self.dirY.text(), self.dirZ.text(), self.c.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                if float(self.dirX.text()) == 0. and float(self.dirY.text()) == 0. and float(self.dirZ.text()) == 0.:
                    raise Exception
                self.ampLabel.setText(str(float(self.amp.text())) + ' Pa')
                self.dirLabel.setText('x ' + str(float(self.dirX.text())) + ' y ' + str(float(self.dirY.text())) + ' z ' + str(float(self.dirZ.text())))
                c = float(self.c.text()) # It's just a check, variable is not used here
                self.generatePressure()
                self.update3DActor()
                self.switch()
            except: # if input is wrong, show message and reset values
                messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                self.resetValues()
        else:
            self.resetValues()
        return var

    def update3DActor(self):
        """
        updates the vtk actors
        """
        # Get model infos
        nodes = self.myModel.nodes
        center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
        # Symbol for plane wave
        # Calculate random directions in the plane
        direction1 = np.cross(loadNormal, [loadNormal[0]+0.11*loadNormal[1], loadNormal[1]+0.22*loadNormal[2], loadNormal[2]+0.33*loadNormal[0]])
        direction1 = direction1/np.linalg.norm(direction1)
        direction2 = np.cross(loadNormal, direction1)
        direction2 = direction2/np.linalg.norm(direction2)
        # Update points of vtk quad object
        [self.loadGridSymbol.GetPoints().SetPoint(p, [center[0] + scaleFactor*loadNormal[0] + scaleFactor*0.2*edge[0], center[1] + scaleFactor*loadNormal[1] + scaleFactor*0.2*edge[1], center[2] + scaleFactor*loadNormal[2] + scaleFactor*0.2*edge[2]]) for p, edge in enumerate([-direction1-direction2, -direction1+direction2, direction1+direction2, direction1-direction2])]
        self.loadGridSymbol.GetPoints().Modified()
        # Update load symbol
        self.arrowDataSymbol.GetPoints().SetPoint(0, center[0] + scaleFactor*loadNormal[0], center[1] + scaleFactor*loadNormal[1], center[2] + scaleFactor*loadNormal[2])
        self.arrowDataSymbol.GetPoints().Modified()
        self.arrowVectorsSymbol.SetTuple(0, [scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
        self.arrowVectorsSymbol.Modified()
        # Update load
        arrowPointLoad = vtk.vtkPoints()

        ### get a lower number of arrows if there are more elements or the element size is small
        try: 
            arrNoScale = int(len(self.surfacePoints)/100.) # draw every 100th arrow in case there are >100 arrows
            if arrNoScale<1:
                arrNoScale = 1
        except: 
            arrNoScale = 1
        [arrowPointLoad.InsertNextPoint([self.surfacePoints[p][0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], self.surfacePoints[p][1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], self.surfacePoints[p][2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p in range(0,len(self.surfacePoints),arrNoScale)]
        #[arrowPointLoad.InsertNextPoint([point[0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], point[1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], point[2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p, point in enumerate(self.surfacePoints)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.1*scaleFactor*vec[0], -0.1*scaleFactor*vec[1], -0.1*scaleFactor*vec[2]]) for vec in self.surfaceElementNormals]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()
