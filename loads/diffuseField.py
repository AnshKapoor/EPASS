from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit
import vtk
import numpy as np
import os
from lxml import etree
from standardWidgets import removeButton, editButton, setupWindow, messageboxOK, progressWindow
from loads import load
import math, cmath, random, time
np.random.seed(int(time.time()))
pi = math.pi
randomize = True


class diffuseField(load):
    """
    class for diffuse field load. provides methods to calculate pressure/phases acc. to load vector and size
    """
    def __init__(self, ak3path, myModel, vtkWindow):
        """
        initialise basic load dependent GUI objects
        """
        super(diffuseField, self).__init__()
        self.ak3path = ak3path
        self.myModel = myModel
        self.removeButton = removeButton(self.ak3path)
        self.editButton = editButton()
        self.type = 'diffuse_field'
        #
        self.amp = QLineEdit('1.')
        self.dirX = QLineEdit('1.')
        self.dirY = QLineEdit('1.')
        self.dirZ = QLineEdit('1.')
        self.c = QLineEdit('340.')
        #
        self.samples = QLineEdit('1000')
        self.radius = QLineEdit('10.')
        self.normal = QLineEdit('0,0,1')
        self.position = QLineEdit('0,0,0')
        #
        self.label = QLabel('Diffuse Field')
        self.ampLabel = QLabel(self.amp.text() + ' Pa')
        self.radLabel = QLabel('Radius: ' + self.radius.text())
        self.sampLabel = QLabel('Sources: ' + self.samples.text())
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.ampLabel, self.radLabel, self.sampLabel, self.drawCheck, self.editButton]]
        #
        self.generatePointCloud()
        self.initSetupWindow()
        self.init3DActor(vtkWindow)
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
        clear all content in diffuseField layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))


    def generatePointCloud(self):
        """
        generates a half sphere point cloud with variable parameters
        """
        #fibonacci
        samples = 2*int(self.samples.text()) ## *2 because initially a sphere is constructed, which is then separated.
        normal = [float(x) for x in list(self.normal.text().split(','))]#[1.,0.,1.]
        R = float(self.radius.text()) # Radius
        center = [int(x) for x in list(self.position.text().split(','))]# Center of Semisphere

        normLength = (float(normal[0])**2+float(normal[1])**2+float(normal[2])**2)**0.5
        normal = [p/normLength for p in normal]

        if normal != [0.,0.,1.]:
            rotAngle = np.arccos(np.dot(normal, [0.,0.,1.]))
            ca = np.cos(rotAngle)
            sa = np.sin(rotAngle)

            rotAxis = np.cross([0.,0.,1.], normal)
            R1 = rotAxis[0]
            R2 = rotAxis[1]
            R3 = rotAxis[2]

        rnd = 1.
        if randomize:
            rnd = random.random() * samples

        points = []
        offset = 2./samples
        increment = math.pi * (3. - math.sqrt(5.));

        for i in range(samples):
            y = ((i * offset) - 1) + (offset / 2);
            r = math.sqrt(1 - pow(y,2))

            phi = ((i + rnd) % samples) * increment

            x = math.cos(phi) * r
            z = math.sin(phi) * r
            if z>=0:
                # Rotation into normal direction
                if normal != [0.,0.,1.]:
                  x_rot = x*(R1**2*(1.-ca)+ca)    + y*(R1*R2*(1.-ca)-R3*sa) + z*(R1*R3*(1.-ca)+R2*sa)
                  y_rot = x*(R1*R2*(1.-ca)+R3*sa) + y*(R2**2*(1.-ca)+ca)    + z*(R2*R3*(1.-ca)-R1*sa)
                  z_rot = x*(R1*R3*(1.-ca)-R2*sa) + y*(R2*R3*(1.-ca)+R1*sa) + z*(R3**2*(1.-ca)+ca)
                else:
                  x_rot = x
                  y_rot = y
                  z_rot = z
                # Addition to final points vector
                points.append([R*x_rot + center[0], R*y_rot + center[1], R*z_rot + center[2]])

        self.sourcePoints = np.array(points)


    def generatePressure(self):
        """
        Calculates pressure excitation on the selected blocks due to the created diffuse field
        """
        c = float(self.c.text()) #get Speed of Sound as number
        frequencies = self.myModel.calculationObjects[0].frequencies
        self.findRelevantPoints() #get values for the middle of every element

        #calculate sound pressure and phase on every element
        if self.surfacePoints is not []:
            self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
            self.surfacePressure = np.zeros((len(frequencies),len(self.surfacePoints)),dtype=complex)
            r_matrix = np.zeros((len(self.sourcePoints), len(self.surfacePoints),)) #matrix will contain distances from each point source to each element
            progWin = progressWindow(len(self.surfacePoints)-1, "Calculating distances")
            for nsp,surfacePoint in enumerate(self.surfacePoints):
                r_matrix[:,nsp] = ((self.sourcePoints[:,0]-surfacePoint[0])**2 + (self.sourcePoints[:,1]-surfacePoint[1])**2 + (self.sourcePoints[:,2]-surfacePoint[2])**2)**0.5
                progWin.setValue(nsp)
                QApplication.processEvents()
            progWin = progressWindow(len(frequencies)-1, "Calculating phases")
            for nf,f in enumerate(frequencies):
                k = 2.*pi*f/c # Wave number
                # with random phase
                randPhase = 2*math.pi*np.random.rand(len(self.sourcePoints)) # random phase per source
                self.surfacePressure[nf,:] = np.sum(np.multiply(1/r_matrix, (np.exp(1j*k*r_matrix).T*np.exp(1j*randPhase)).T), axis=0)
                # without random phase
                #self.surfacePressure[nf,:] = np.sum(np.multiply(1/r_matrix, np.exp(1j*k*r_matrix)), axis=0)
                for ne in range(len(self.surfacePoints)):
                    self.surfacePhases[nf,ne] = cmath.phase(self.surfacePressure[nf,ne])
                    progWin.setValue(nf)
                    QApplication.processEvents()#transition from complex pressure to phase


    def getXYdata(self):
        """
        Return x, y data for plotting; for plane wave: constant amplitude
        """
        return self.myModel.calculationObjects[0].frequencies, len(self.myModel.calculationObjects[0].frequencies)*[float(self.amp.text())]


    def init3DActor(self, vtkWindow):
        """
        initialize vtk objects
        """
        # Get model infos
        nodes = self.myModel.calculationObjects[0].nodes
        center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:,1])-min(nodes[:,1])), abs(max(nodes[:,2])-min(nodes[:,2])), abs(max(nodes[:,3])-min(nodes[:,3]))] )
        #
        arrowSource = vtk.vtkArrowSource()
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
        # Half sphere Point Cloud
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetRadius(0.05)
        self.sphereDataLoad = vtk.vtkPolyData()
        spherePointsLoad = vtk.vtkPoints()
        self.sphereDataLoad.SetPoints(spherePointsLoad)
        # Glyph for load symbol
        glyphLoad1 = vtk.vtkGlyph3D()
        glyphLoad1.SetScaleModeToScaleByVector()
        glyphLoad1.SetSourceConnection(sphereSource.GetOutputPort())
        glyphLoad1.SetInputData(self.sphereDataLoad)
        glyphLoad1.Update()
        # Mapper for load
        self.sphereMapperLoad = vtk.vtkPolyDataMapper()
        self.sphereMapperLoad.SetInputConnection(glyphLoad1.GetOutputPort())
        # Actor for load
        self.sphereActorLoad = vtk.vtkActor()
        self.sphereActorLoad.GetProperty().SetColor(1., 0.3, 0.) ##Rot
        self.sphereActorLoad.SetMapper(self.sphereMapperLoad)

        #List of Actors for iteration in vtkWindow
        self.actorsList = [self.arrowActorLoad, self.sphereActorLoad]


    def initSetupWindow(self):
        """
        basic objects for the individual setup window
        """
        self.setupWindow = setupWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Amplitude'), self.amp)
        self.setupWindow.layout.addRow(QLabel('Speed of Sound'), self.c)
        self.setupWindow.layout.addRow(QLabel('Radius of Half Sphere'), self.radius)
        self.setupWindow.layout.addRow(QLabel('No. of Point Sources'), self.samples)
        self.setupWindow.layout.addRow(QLabel('Origin of Point Cloud x,y,z'), self.position)
        self.setupWindow.layout.addRow(QLabel('Normal dir. of Point Cloud x,y,z'), self.normal)
        #
        self.blockChecker = []
        for block in self.myModel.calculationObjects[0].elems:
            self.blockChecker.append(QCheckBox())
            self.setupWindow.blockLayout.addRow(self.blockChecker[-1], QLabel('Block ' + str(block[1]) + ' (' + str(block[0]) + ')'))
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())


    def resetValues(self):
        """
        resets parameter values
        """
        for n, item in enumerate([self.amp, self.dirX, self.dirY, self.dirZ, self.c, self.samples, self.radius, self.normal, self.position]):
            item.setText(self.varSave[n])


    def showEdit(self):
        """
        recalculates data with new input parameters
        """
        self.varSave = [self.amp.text(), self.dirX.text(), self.dirY.text(), self.dirZ.text(), self.c.text(), self.samples.text(), self.radius.text(), self.normal.text(), self.position.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                if float(self.radius.text()) == 0. and float(self.samples.text()) == 0.:
                    raise Exception
                self.ampLabel.setText(str(float(self.amp.text())) + ' Pa')
                self.radLabel.setText('Radius: ' + self.radius.text())
                self.sampLabel.setText('Sources: ' + self.samples.text())
                c = float(self.c.text()) # It's just a check, variable is not used here
                self.generatePressure()
                self.generatePointCloud()
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
        nodes = self.myModel.calculationObjects[0].nodes
        center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        scaleFactor = max( [abs(max(nodes[:,1])-min(nodes[:,1])), abs(max(nodes[:,2])-min(nodes[:,2])), abs(max(nodes[:,3])-min(nodes[:,3]))] )

        # Update load
        arrowPointLoad = vtk.vtkPoints()

        ### get a lower number of arrows if there are more elements or the element size is small
        numberOfElem = len((self.myModel.calculationObjects[0].elems[0][2]))
        arrNoScale = int(numberOfElem/32)#number 32 can be changed
        if arrNoScale<1:
            arrNoScale = 1
        [arrowPointLoad.InsertNextPoint([self.surfacePoints[p][0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], self.surfacePoints[p][1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], self.surfacePoints[p][2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p in range(0,len(self.surfacePoints),arrNoScale)]
        #[arrowPointLoad.InsertNextPoint([point[0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], point[1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], point[2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p, point in enumerate(self.surfacePoints)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.1*scaleFactor*vec[0], -0.1*scaleFactor*vec[1], -0.1*scaleFactor*vec[2]]) for vec in self.surfaceElementNormals]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()

        # Update Half Sphere Point Cloud
        spherePointsLoad = vtk.vtkPoints()
        [spherePointsLoad.InsertNextPoint([point[0], point[1], point[2]]) for p, point in enumerate(self.sourcePoints)]
        self.sphereDataLoad.SetPoints(spherePointsLoad)
        self.sphereDataLoad.Modified()
