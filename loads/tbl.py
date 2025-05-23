#
import vtkplotlib as vtkplt
import json
from PyQt5.QtWidgets import QApplication, QLabel, QWidgetItem, QCheckBox, QLineEdit, QFileDialog, QComboBox, QHBoxLayout
import vtk
import numpy as np
from vtk.util.numpy_support import numpy_to_vtk
import math
from standardWidgets import ak3LoadButton, removeButton, editButton, setupLoadWindow, messageboxOK, progressWindow
from standardFunctionsGeneral import isPlateType
from loads import elemLoad
import time
np.random.seed(int(time.time()))
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 16})
from matplotlib.colors import LogNorm
import scipy as sp

# tbl load
class tbl(elemLoad):
    def __init__(self, myModel):
        super(tbl, self).__init__()
        self.myModel = myModel
        self.removeButton = removeButton()
        self.editButton = editButton()
        self.type = 'Turbulent_Boundary_Layer'
        #
        self.dirX = QLineEdit('0.')
        self.dirY = QLineEdit('0.')
        self.dirZ = QLineEdit('1.')
        self.flowDirX = QLineEdit('1.')
        self.flowDirY = QLineEdit('0.')
        self.flowDirZ = QLineEdit('0.')
        self.randomSelector = QComboBox()
        [self.randomSelector.addItem(x) for x in ['no', 'per data point', 'per element', 'coherence grid']]
        self.shapeCraft = QComboBox()
        [self.shapeCraft.addItem(x) for x in ['Cylindrical', 'Cubic', 'Arbitrary']]
        self.loadButton = ak3LoadButton()
        self.loadButton.clicked.connect(self.getFilename)
        self.dataPoints = []
        #
        self.label = QLabel('Turbulent Boundary Layer')
        self.dirLabel = QLabel('x ' + self.flowDirX.text() + ' y ' + self.flowDirY.text() + ' z ' + self.flowDirZ.text())
        self.drawCheck = QCheckBox('Draw')
        self.drawCheck.setStatusTip('Show load in 2D Graph and 3D Window')
        self.drawCheck.clicked.connect(self.switch)
        #
        [self.addWidget(wid) for wid in [self.removeButton, self.label, self.dirLabel, self.drawCheck, self.editButton]]
        #
        self.initSetupWindow()
        self.init3DActor()
        # A switch indicating a new setup within this load
        self.changeSwitch = QCheckBox()
        self.changeSwitch.setChecked(0)
        # Constant Efimtsov parameters according to fitting in Haxter, JSV 390(2017): 86-117
        self.a1 = 0.071
        self.a2 = 4.1
        self.a3 = 0.26
        self.a4 = 0.66
        self.a5 = 39.0
        self.a6 = 9.9
        #
        self.editButton.clicked.connect(self.showEdit)
        var = self.showEdit()
        if var == 0: # is the case if the initial setup window is canceled by the user
            self.generatePressure()
            self.update3DActor()
    #
    def calcEfimtsovCoherenceLengths(self, omega, delta, uTau, uC):
        Sh = omega*delta/uTau # Strouhal number for Efimtsov
        quot1 = uC/uTau
        quot2 = self.a2/self.a3
        quot3 = self.a5/self.a6
        # Coherence lengths
        Lx = delta * ((self.a1*Sh/quot1)**2 + self.a2**2 / (Sh**2 + quot2**2))**-0.5
        Ly = delta * ((self.a4*Sh/quot1)**2 + self.a5**2 / (Sh**2 + quot3**2))**-0.5
        return Lx, Ly
    #
    def calcEfimtsovIntensity(self, kX, kY, omega, uC, Lx, Ly):
        alphaX = uC/(omega*Lx)
        alphaY = uC/(omega*Ly)
        P1 = 4.*alphaX*alphaY
        P2 = alphaY**2. + np.power(np.array(kY)*uC/omega, 2.)
        P3 = alphaX**2. + np.power(np.array(kX)*uC/omega - 1., 2.)
        spectrumFactor = (uC/omega)**2. / (2.*math.pi)**2.
        return spectrumFactor*P1/(P2[:,None]*P3)
    #
    def calc_uC(self, freq, uInf):
        if freq<475.:
            return 0.9*uInf # Haxter und Spehr 2012
        elif freq>5000.:
            return 0.75*uInf
        else:
            return (0.9 - 0.15*(freq-475.)/4525.) * uInf
    #
    def clearLayout(self):
        """
        Clear all content in planeWave layout
        """
        for i in reversed(range(self.count())):
            if isinstance(self.itemAt(i), QWidgetItem):
                self.takeAt(i).widget().setParent(None)
            else:
                self.removeItem(self.contLayout.takeAt(i))
    #
    def generatePressure(self):
        """
        Calculates pressure excitation on the selected blocks according to Klabes internoise 2016 (autospectrum) and Efimtsov (Wavenumber-spectrum) due to a turbulent boundary layer
        """
        frequencies = self.myModel.frequencies
        self.findRelevantPoints()
        if self.surfacePoints is not []:
            self.surfacePhases = np.zeros((len(frequencies),len(self.surfacePoints)))
            self.surfaceAmps = np.zeros((len(frequencies),len(self.surfacePoints)))
            if self.dataPoints==[]:
                messageboxOK('Error', 'No parameter input file loaded.\nNo calculation possible!\n')
            else:
                self.nearestNeighbor()
                # Get model infos
                #nodes = self.myModel.nodes
                #center = [0.5*(max(nodes[:,1]) + min(nodes[:,1])), 0.5*(max(nodes[:,2]) + min(nodes[:,2])), 0.5*(max(nodes[:,3]) + min(nodes[:,3]))]
                flowDir = [float(self.flowDirX.text()), float(self.flowDirY.text()), float(self.flowDirZ.text())]
                flowDir = flowDir/np.linalg.norm(flowDir)
                # Calculate distances in direction of the flow
                progWin = progressWindow(len(self.surfacePoints)-1, "Calculating TBL load")
                x0 = 0.
                y0 = 0.
                surfacePointPrior=[0,0,0]
                totalDistance=0
                for nsp, surfacePoint in enumerate(self.surfacePoints):
                    # Calculate: AMPS according to Klabes 2017 ; PHASES using Efimtsov model
                    idx = self.euclNearestDataPoint[nsp] # index of dataPoint (loaded before via json file) which is nearest to current surfacePoint
                    delta = self.par_delta[idx]
                    uE = self.par_uE[idx]
                    MA = self.par_MA[idx]
                    c0 = self.par_c0[idx]
                    tauW = self.par_tauW[idx]
                    eta = self.par_eta[idx]
                    rho = self.par_rho[idx]
                    TKE = self.par_TKE[idx]
                    FL = self.par_FL[idx]
                    dcpdx = self.par_dcpdx[idx]
                    uTau = (tauW/rho)**0.5
                    uInf = c0 * MA
                    nu = eta / rho # kin. viscosity
                    cf = 2*(uTau/uInf)**2
                    #
                    if self.randomSelector.currentText()=='per element':
                        x0 = np.random.rand()*1000.
                        y0 = np.random.rand()*1000.
                    if self.randomSelector.currentText()=='per data point':
                        x0 = self.rand_x0[idx]
                        y0 = self.rand_y0[idx]
                    for nf, freq in enumerate(frequencies):
                        if self.randomSelector.currentText()=='coherence grid':
                            # currentGrid contains a midpoint in 2D (2 cylindrical coordinates - x for lengthwise position on aircraft skin and y for phi (radius does not matter)) and a random origin (coords 3-4)
                            currentGrid = self.myModel.allGrids[nf] 
                            # find nearest midpoint in grid to current surface point
                            #surfacePointCylindrical = (np.arcsin(surfacePoint[1]/self.R) * surfacePoint[2]/abs(surfacePoint[2]) * self.R)
                            #midpointIdx = np.argmin(np.abs(currentGrid[:,0] - surfacePoint[0]) + np.abs(currentGrid[:,1] - surfacePointCylindrical) )
                            midpointIdx = np.argmin(np.abs(currentGrid[:,0] - surfacePoint[0]) + np.abs(currentGrid[:,1] - surfacePoint[1]) + np.abs(currentGrid[:,2] - surfacePoint[2]) )
                            x0 = currentGrid[midpointIdx,3]
                            y0 = currentGrid[midpointIdx,4]
                        omega = 2.*math.pi*freq
                        ### Klabes 2017
                        #gammaM = 2661.7*MA**2 - 3504.2*MA + 3622.4 + 3.6e-2*FL**2 - 22.5*FL
                        #gammaC = -1.3845*MA - 0.7182 - 4.5031e-5*FL**2 + 2.7361e-2*FL
                        #gammaDG = gammaM*cf + gammaC
                        #a = (TKE / 10.)**gammaDG
                        #b = 0.5
                        #betaDeltaL = delta * dcpdx
                        #ReDeltaL = delta*uE/nu
                        #c = 2.7 + 3*betaDeltaL - (6e-10*(0.7*ReDeltaL**0.6 - 2700.)**3. + 0.02)
                        #d = 12. + 2.39*math.log(ReDeltaL**0.53 * betaDeltaL**2., 10.)
                        #betaDDeltaL = delta * dcpdx * (2./cf)**0.5
                        #e = 0.675 + 0.11428*betaDDeltaL + (7e-11*(ReDeltaL**0.6 - 3750.)**3. - 0.01)
                        #f = 1.1
                        #g = -0.57
                        #h = 5.5
                        ### Klabes 2016 internoise
                        betaDeltaL = delta * dcpdx
                        betaDDeltaL = (delta * dcpdx) * (2./cf)**0.5
                        ReDeltaL = delta*uE/nu
                        ReDDeltaL = (delta*uE/nu) * (2./cf)**0.5
                        gammaDG = (-592.71*cf + 1.74)*ReDDeltaL**0.01
                        a = (TKE / 10.)**gammaDG
                        b = 0.5
                        c = 1.35 + 3*betaDeltaL
                        d = ReDeltaL**0.174 - 6.7
                        e = -0.11428*betaDDeltaL + 1.55
                        f = 1.1
                        g = -0.57
                        h = 5.5
                        #
                        Rt = (delta/uE)/(nu/uTau**2.)
                        scalingFactor = ((tauW**2.)*delta)/uE
                        P0 = 2.*math.pi*freq*delta/uE
                        P1 = a*P0**b
                        P2 = (P0**c + d)**e
                        P3 = (f*(Rt**g)*P0)**h
                        phi = scalingFactor*P1/(P2 + P3)
                        self.surfaceAmps[nf,nsp] = phi**0.5
                        ### Efimtsov; Fitted constants a1-a6 according to Haxter, JSV 390(2017): 86-117
                        uC = self.calc_uC(freq, uInf)
                        Lx, Ly = self.calcEfimtsovCoherenceLengths(omega, delta, uTau, uC)
                        #
                        kC = omega/uC
                        steps = 200
                        dK = 20*kC/(steps-1)
                        kRange = np.linspace(-5*kC,5*kC,steps)[:-1] + dK/2. # Midpoint in discrete intervals
                        #
                        eX = np.tile(np.exp(1j*kRange*(surfacePoint[0]-x0)), (len(kRange), 1))
                        distanceBetween=np.sqrt((surfacePoint[1]-surfacePointPrior[1])**2+(surfacePoint[2]-surfacePointPrior[2])**2)
                        totalDistance=totalDistance+distanceBetween
                        if self.randomSelector.currentText()=='coherence grid': 
                            #eY = np.tile(np.exp(1j*kRange*(surfacePointCylindrical-y0))[:,None], (1, len(kRange)))
                            eY = np.tile(np.exp(1j*kRange*(totalDistance-y0))[:,None], (1, len(kRange)))
                        else:
                            eY = np.tile(np.exp(1j*kRange*(totalDistance-y0))[:,None], (1, len(kRange)))
                        phaseMatrix = eX+eY
                        #
                        surfacePointPrior=surfacePoint
                        densMatrix = self.calcEfimtsovIntensity(kRange, kRange, omega, uC, Lx, Ly)
#                        globMin = np.amin(np.amin(densMatrix))
#                        print(globMin)
#                        globMax = np.amax(np.amax(densMatrix))
#                        print(globMax)
#                        print(freq)
#                        plt.figure(figsize=(10,7))
#                        plt.pcolor(kRange/kC, kRange/kC, densMatrix, norm=LogNorm(), cmap='Greys', vmin=globMin, vmax=globMax)
#                        plt.colorbar(label='$\Phi_{norm}$')
#                        plt.xlabel('$k_x$/$k_\omega$')
#                        plt.ylabel('$k_y$/$k_\omega$')
#                        plt.savefig('C:\scratch\AP2\plotWaveSpec'+str(freq)+'.png')
                        #plt.show()
                        #print(C)
                        superimpWave = densMatrix * phaseMatrix
                        #
                        phase = np.angle(np.sum(np.sum(superimpWave)))
                        # Set range from 0 to 2pi
                        if phase<0.:
                            self.surfacePhases[nf,nsp] = 2*math.pi + phase
                        else:
                            self.surfacePhases[nf,nsp] = phase
                        #
                        progWin.setValue(nsp)
                        QApplication.processEvents()
    #
    def getFilename(self):
        """
        Open menu to choose file which contains point data for tbl parameters
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(None,"QFileDialog.getOpenFileName()", "","All Files (*);;json Files (*.json)", options=options)
        if fileName:
          self.filename = fileName
          self.loadData(fileName) #calls loadData function to read the file
    #
    def getXYdata(self):
        """
        Return x, y data for plotting; for tbl load: mean amplitude per frequency
        """
        return self.myModel.frequencies, np.mean(self.surfaceAmps, axis=1), 'TBL'
    #
    def init3DActor(self):
        """
        initialize vtk objects of this load
        """
        # Get model infos
        nodes = self.myModel.nodes
        center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        flowDir = [float(self.flowDirX.text()), float(self.flowDirY.text()), float(self.flowDirZ.text())]
        flowDir = flowDir/np.linalg.norm(flowDir)
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
        # Symbol for normal direction of load
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
        # Arrow for normal direction of load and flow direction (3 arrows)
        self.arrowDataSymbol = vtk.vtkPolyData()
        arrowPointsSymbol = vtk.vtkPoints()
        arrowPointsSymbol.InsertNextPoint(center[0] + scaleFactor*loadNormal[0], center[1] + scaleFactor*loadNormal[1], center[2] + scaleFactor*loadNormal[2])
        arrowPointsSymbol.InsertNextPoint(center[0] + scaleFactor*flowDir[0],    center[1] + scaleFactor*flowDir[1],    center[2] + scaleFactor*flowDir[2])
        self.arrowDataSymbol.SetPoints(arrowPointsSymbol)
        self.arrowVectorsSymbol = vtk.vtkDoubleArray()
        self.arrowVectorsSymbol.SetNumberOfComponents(3)
        self.arrowVectorsSymbol.InsertNextTuple([scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
        self.arrowVectorsSymbol.InsertNextTuple([scaleFactor*-0.2*flowDir[0],    scaleFactor*-0.2*flowDir[1],    scaleFactor*-0.2*flowDir[2]])
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
    #
    def initSetupWindow(self):
        """
        basic objects for the individual setup window
        """
        self.setupWindow = setupLoadWindow(self.label.text())
        # ADD TO LAYOUT
        self.setupWindow.layout.addRow(QLabel('Norm-Direction X'), self.dirX)
        self.setupWindow.layout.addRow(QLabel('Norm-Direction Y'), self.dirY)
        self.setupWindow.layout.addRow(QLabel('Norm-Direction Z'), self.dirZ)
        self.setupWindow.layout.addRow(QLabel('Flow-direction X'), self.flowDirX)
        self.setupWindow.layout.addRow(QLabel('Flow-direction Y'), self.flowDirY)
        self.setupWindow.layout.addRow(QLabel('Flow-direction Z'), self.flowDirZ)
        self.setupWindow.layout.addRow(QLabel('Use Random'),       self.randomSelector)
        self.setupWindow.layout.addRow(QLabel('Shape'),            self.shapeCraft)
        self.setupWindow.layout.addRow(QLabel('Load xyz input file'), self.loadButton)
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
        self.setupWindow.blockLayout.addStretch()
        #
        self.setupWindow.setFixedSize(self.setupWindow.mainLayout.sizeHint())
    #
    def loadData(self, filename):
        """
        Loads file with x,y,z flow data for Klabes and Efimtsov parameter.
        Must be .json and must be a dict like:
        {"pointdata":[
          {"coord":[4.00,1.75,0.00], "delta":0.028, "uE":259.25, "MA":0.78, "c0":295.042, "tauW":21.057, "eta":14.3226e-6, "rho":0.274, "TKE":260.2, "FL":370.0, "dcpdx":0.04016},
          {"coord":[6.00,1.75,0.00], "delta":0.058, "uE":241.41, "MA":0.78, "c0":295.042, "tauW":15.737, "eta":14.3226e-6, "rho":0.296, "TKE":218.1, "FL":370.0, "dcpdx":0.06914},
          ...
        ]}
        """
        with open(filename) as f:
            ld = json.load(f)
        #
        self.dataPoints = []
        #
        self.par_delta = []
        self.par_uE = []
        self.par_MA = []
        self.par_c0 = []
        self.par_tauW = []
        self.par_eta = []
        self.par_rho = []
        self.par_TKE = []
        self.par_FL = []
        self.par_dcpdx = []
        #
        self.rand_x0 = []
        self.rand_y0 = []
        self.rand_z0 = []
        #
        for point in ld.get('pointdata'):
            self.dataPoints.append(point.get('coord'))
            self.par_delta.append(float(point.get('delta')))
            self.par_uE.append(float(point.get('uE')))
            self.par_MA.append(float(point.get('MA')))
            self.par_c0.append(float(point.get('c0')))
            self.par_tauW.append(float(point.get('tauW')))
            self.par_eta.append(float(point.get('eta')))
            self.par_rho.append(float(point.get('rho')))
            self.par_TKE.append(float(point.get('TKE')))
            self.par_FL.append(float(point.get('FL')))
            self.par_dcpdx.append(float(point.get('dcpdx')))
            # Each point gets a random origin (later used if user selects a random origin per data point)
            self.rand_x0.append(np.random.rand()*1000.)
            self.rand_y0.append(np.random.rand()*1000.)
            self.rand_z0.append(np.random.rand()*1000.)
        # Create coherence grid according to Efimtsov coherence lengths with random origin per grid point (later used if user selects a random origin in that grid)
        frequencies = self.myModel.frequencies
        progWin = progressWindow(len(frequencies)-1, "Creating coherence grid")
        if self.shapeCraft.currentText()=='Cylindrical':
            #self.R = 1.78 # Radius
            #Hard coded coordinates for Radius, depends on how it is turned!
            self.R=np.sqrt(self.myModel.nodes[0]['yCoords']**2+self.myModel.nodes[0]['zCoords']**2)

            startX = min([x[0] for x in self.dataPoints])
            endX = max([x[0] for x in self.dataPoints])
            startPhi = -2*self.R*math.pi/4.
            endPhi = 2*self.R*math.pi/4.
            totalPhi  = endPhi-startPhi
            self.myModel.allGrids = []
            for nf, freq in enumerate(frequencies):
                currentGrid = np.empty((0,4))
                currentX = startX
                omega = 2*math.pi*freq
                #
                while 1:
                    # Calc coherence lengths according to Efimtsov at current position for current frequency
                    idx = np.argmin([abs(dataPoint[0] - currentX) for dataPoint in np.array(self.dataPoints)])
                    delta = self.par_delta[idx]
                    MA = self.par_MA[idx]
                    c0 = self.par_c0[idx]
                    tauW = self.par_tauW[idx]
                    rho = self.par_rho[idx]
                    uTau = (tauW/rho)**0.5
                    uC = self.calc_uC(freq, c0*MA)
                    Lx, Ly = self.calcEfimtsovCoherenceLengths(omega, delta, uTau, uC)
                    if currentX+Lx > endX:
                        phiGrid = np.linspace(startPhi, endPhi, round(totalPhi / Ly))
                        yMidpoints = np.array(0.5*(phiGrid[1:] + phiGrid[:-1]))
                        xMidpoints = np.array(len(yMidpoints) * [0.5*(currentX+endX)])
                        currentGrid = np.concatenate((currentGrid, np.column_stack((xMidpoints, yMidpoints, np.random.rand(len(yMidpoints))*1000., np.random.rand(len(yMidpoints))*1000.))))
                        break
                    else:
                        phiGrid = np.linspace(startPhi, endPhi, round(totalPhi / Ly))
                        yMidpoints = np.array(0.5*(phiGrid[1:] + phiGrid[:-1]))
                        xMidpoints = np.array(len(yMidpoints) * [currentX + 0.5*Lx])
                        currentGrid = np.concatenate((currentGrid, np.column_stack((xMidpoints, yMidpoints, np.random.rand(len(yMidpoints))*1000., np.random.rand(len(yMidpoints))*1000.))))
                        currentX = currentX + Lx
            #
                self.myModel.allGrids.append(currentGrid)
                progWin.setValue(nf)
                QApplication.processEvents()
            
        elif self.shapeCraft.currentText()=='Arbitrary':
            #self.R = 1.78 # Radius
            #Hard coded coordinates for Radius, depends on how it is turned!
            self.R=np.sqrt(self.myModel.nodes[0]['yCoords']**2+self.myModel.nodes[0]['zCoords']**2)

            startX = min([x[0] for x in self.dataPoints])
            endX = max([x[0] for x in self.dataPoints])
            startPhi = -2*self.R*math.pi/4.
            endPhi = 2*self.R*math.pi/4.
            totalPhi  = endPhi-startPhi
            self.myModel.allGrids = []
            self.myModel.currLyMid=[]

            #depends on how the model is situated (z-Axis a.so.)
            self.findRelevantPoints()
            indexCurve=[]
            tol=0.05
            lengthAxis='z'
            if lengthAxis=='x':
                plotIndexes=[0,2,1]
            elif lengthAxis=='z':
                plotIndexes=[2,0,1]

            # if z axis is long axis -> use [:,0],[:,1] in indexing
            #indexCurve.append([idx for idx,n in enumerate(self.surfacePoints) if np.abs(n[2]-self.surfacePoints[0][2])<=tol])
            # for x axis as long axis -> use [:,1],[:,2] in indexing
            indexCurve.append([idx for idx,n in enumerate(self.surfacePoints) if np.abs(n[plotIndexes[0]]-self.surfacePoints[0][plotIndexes[0]])<=tol])
            #
            indexCurve = np.array(indexCurve).flatten().astype(int)
            surfacePoints = np.array(self.surfacePoints)
            curveNodes=surfacePoints[indexCurve,:]
            curveNodes=curveNodes[np.argsort(curveNodes[:,plotIndexes[1]])]
            if lengthAxis=='z':
                curveNodes=curveNodes[12:,:]
            dist1=curveNodes[1:,plotIndexes[1]]-curveNodes[:-1,plotIndexes[1]]
            dist2=curveNodes[1:,plotIndexes[2]]-curveNodes[:-1,plotIndexes[2]]
            dist1[0]=2*dist1[0]
            dist2[0]=2*dist2[0]
            dist=np.sum(np.sqrt(dist1**2+dist2**2))
            distvec=np.column_stack((dist1,dist2))
            distbetween=np.sqrt(dist1**2+dist2**2)
            distvec[:,0]=distvec[:,0]/distbetween
            distvec[:,1]=distvec[:,1]/distbetween
            distvec=distvec/100
            plt.plot(curveNodes[:,plotIndexes[1]],curveNodes[:,plotIndexes[2]])
            #plt.show()
            for nf, freq in enumerate(frequencies):
                currentGrid = np.empty((0,5))
                currentX = startX
                omega = 2*math.pi*freq
                currLyMid1=[]
                currLyMid2=[]
                currLyMid1.append(-1.61)
                currLyMid2.append(0.1)
                currLyMid1.append(curveNodes[0,plotIndexes[1]])
                currLyMid2.append(curveNodes[0,plotIndexes[2]])

                #
                while 1:
                    # Calc coherence lengths according to Efimtsov at current position for current frequency
                    idx = np.argmin([abs(dataPoint[0] - currentX) for dataPoint in np.array(self.dataPoints)])
                    delta = self.par_delta[idx]
                    MA = self.par_MA[idx]
                    c0 = self.par_c0[idx]
                    tauW = self.par_tauW[idx]
                    rho = self.par_rho[idx]
                    uTau = (tauW/rho)**0.5
                    uC = self.calc_uC(freq, c0*MA)
                    Lx, Ly = self.calcEfimtsovCoherenceLengths(omega, delta, uTau, uC)
                    i=1
                    jdx=0
                    while currLyMid1[-1]<curveNodes[-1,plotIndexes[1]] :
                        if distvec[jdx,0]==0:
                            distvec[jdx,0]=1e-10
                        if distvec[jdx,1]==0:
                            distvec[jdx,1]=0.00000001
                        if currLyMid1[-1]+Ly*distvec[jdx,0]<=curveNodes[jdx+1,plotIndexes[1]]:
                            if i==1:
                                currLyMid1.append(currLyMid1[-1]+Ly/2*distvec[jdx,0])
                                currLyMid2.append(currLyMid2[-1]+Ly/2*distvec[jdx,1])
                                i=i+1
                            else:
                                currLyMid1.append(currLyMid1[-1]+Ly*distvec[jdx,0])
                                currLyMid2.append(currLyMid2[-1]+Ly*distvec[jdx,1])
                                i=i+1
                        else:
                            if i==1:
                                currLyMid1.append(currLyMid1[-1]+Ly/2*distvec[jdx+1,0])
                                currLyMid2.append(currLyMid2[-1]+Ly/2*distvec[jdx+1,1])
                                i=i+1
                            else:
                                currLyMid1.append(currLyMid1[-1]+Ly*distvec[jdx,0])
                                currLyMid2.append(currLyMid2[-1]+Ly*distvec[jdx,1])
                                i=i+1
                            jdx=jdx+1   
                    if currentX+Lx > endX:
                        phiGrid = np.linspace(startPhi, endPhi, round(totalPhi / Ly))
                        yMidpoints = np.array(0.5*(phiGrid[1:] + phiGrid[:-1]))
                        xMidpoints = np.array(len(currLyMid1) * [0.5*(currentX+endX)])
                        currentGrid = np.concatenate((currentGrid, np.column_stack((xMidpoints, currLyMid1,currLyMid2, np.random.rand(len(currLyMid1))*1000., np.random.rand(len(currLyMid1))*1000.))))
                        break
                    else:
                        phiGrid = np.linspace(startPhi, endPhi, round(totalPhi / Ly))
                        yMidpoints = np.array(0.5*(phiGrid[1:] + phiGrid[:-1]))
                        xMidpoints = np.array(len(currLyMid1) * [currentX + 0.5*Lx])
                        currentGrid = np.concatenate((currentGrid, np.column_stack((xMidpoints, currLyMid1,currLyMid2, np.random.rand(len(currLyMid1))*1000., np.random.rand(len(currLyMid1))*1000.))))
                        currentX = currentX + Lx
            #   
                currLyMid1=currLyMid1[::100]
                currLyMid2=currLyMid2[::100]
                currLyMid=np.column_stack((currLyMid1,currLyMid2))   
                self.myModel.currLyMid.append(currLyMid)
                self.myModel.allGrids.append(currentGrid)
                progWin.setValue(nf)
                QApplication.processEvents()
                
    #
    def nearestNeighbor(self):
        """
        finds next elements to given data points, writes into a proximity list, which can then be applied to the elements list
        """
        self.euclNearestDataPoint = []
        for m, surfPoint in enumerate(np.array(self.surfacePoints)):
            # Calculates dist to each loaded dataPoint and saves the index of the  nearest dataPoint
            self.euclNearestDataPoint.append(np.argmin([np.sum(np.square(dataPoint - surfPoint)) for n, dataPoint in enumerate(np.array(self.dataPoints))]))
    #
    def resetValues(self):
        for n, item in enumerate([self.dirX, self.dirY, self.dirZ, self.flowDirX, self.flowDirY, self.flowDirZ]):
            item.setText(self.varSave[n])
    #
    def showEdit(self):
        self.varSave = [self.dirX.text(), self.dirY.text(), self.dirZ.text(), self.flowDirX.text(), self.flowDirY.text(), self.flowDirZ.text()]
        var = self.setupWindow.exec_()
        if var == 0: # reset values
            self.resetValues()
        elif var == 1: # set new values
            try:
                if float(self.dirX.text()) == 0. and float(self.dirY.text()) == 0. and float(self.dirZ.text()) == 0.:
                    raise Exception
                if float(self.flowDirX.text()) == 0. and float(self.flowDirY.text()) == 0. and float(self.flowDirZ.text()) == 0.:
                    raise Exception
                self.dirLabel.setText('x ' + self.flowDirX.text() + ' y ' + self.flowDirY.text() + ' z ' + self.flowDirZ.text())
                #self.generatePressure()
                #self.update3DActor()
                self.switch()
            except: # if input is wrong, show message and reset values
                messageboxOK('Error', 'Wrong input (maybe text instead of numbers or a zero vector?)!')
                self.resetValues()
            self.generatePressure()
            self.update3DActor()
        else:
            self.resetValues()
        return var

    # Method changing the objects changedSwitch in order to indicate 2D and 3D update
    def switch(self):
        if self.changeSwitch.isChecked():
            self.changeSwitch.setChecked(0)
        else:
            self.changeSwitch.setChecked(1)
    #
    def update3DActor(self):
        """
        updates the vtk actors
        """
        # Get model infos
        nodes = self.myModel.nodes
        center = [0.5*(max(nodes[:]['xCoords']) + min(nodes[:]['xCoords'])), 0.5*(max(nodes[:]['yCoords']) + min(nodes[:]['yCoords'])), 0.5*(max(nodes[:]['zCoords']) + min(nodes[:]['zCoords']))]
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        flowDir = [float(self.flowDirX.text()), float(self.flowDirY.text()), float(self.flowDirZ.text())]
        flowDir = flowDir/np.linalg.norm(flowDir)
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
        self.arrowDataSymbol.GetPoints().SetPoint(1, center[0] + scaleFactor*flowDir[0],    center[1] + scaleFactor*flowDir[1],    center[2] + scaleFactor*flowDir[2])
        self.arrowDataSymbol.GetPoints().Modified()
        self.arrowVectorsSymbol.SetTuple(0, [scaleFactor*-0.2*loadNormal[0], scaleFactor*-0.2*loadNormal[1], scaleFactor*-0.2*loadNormal[2]])
        self.arrowVectorsSymbol.SetTuple(1, [scaleFactor*-0.2*flowDir[0],    scaleFactor*-0.2*flowDir[1],    scaleFactor*-0.2*flowDir[2]])
        self.arrowVectorsSymbol.Modified()
        # Update load
        arrowPointLoad = vtk.vtkPoints()
        [arrowPointLoad.InsertNextPoint([point[0] + 0.1*scaleFactor*self.surfaceElementNormals[p][0], point[1] + 0.1*scaleFactor*self.surfaceElementNormals[p][1], point[2] + 0.1*scaleFactor*self.surfaceElementNormals[p][2]]) for p, point in enumerate(self.surfacePoints)]
        self.arrowDataLoad.SetPoints(arrowPointLoad)
        arrowVectorsLoad = vtk.vtkDoubleArray()
        arrowVectorsLoad.SetNumberOfComponents(3)
        [arrowVectorsLoad.InsertNextTuple([-0.1*scaleFactor*vec[0], -0.1*scaleFactor*vec[1], -0.1*scaleFactor*vec[2]]) for vec in self.surfaceElementNormals]
        self.arrowDataLoad.GetPointData().SetVectors(arrowVectorsLoad)
        self.arrowDataLoad.Modified()
        # Draw Scatterplot of Coherence Grid Midpoints for the first frequency in order to check shape only cylinder
         #change x an z coordinates for aircraft model -> How can we generalize that righ coordinates are taken?? -> change in Jason!!
        myModel=np.zeros((len(nodes),3))
        myModel[:,0]=nodes[:]['zCoords']
        myModel[:,1]=nodes[:]['xCoords']
        myModel[:,2]=nodes[:]['yCoords']
        currentGrid = self.myModel.allGrids[0]
        currentGrid = currentGrid[:,0:3]
        currentGrid=np.array(currentGrid)
        #anglephi=currentGrid[:,1]/self.R
        #currentGrid[:,1]=self.R*np.cos(anglephi)
        #currentGrid[:,2]=self.R*np.sin(anglephi)
        #plotGrid1=currentGrid[:,0]
        #plotGrid2=currentGrid[:,1]
        #plotGrid3=currentGrid[:,2]
        #currentGrid[:,0]=plotGrid1
        #currentGrid[:,1]=plotGrid2
        #currentGrid[:,2]=plotGrid3
        currLyMid=self.myModel.currLyMid[0]
        plt.scatter(currLyMid[:,0],currLyMid[:,1])
        plt.show()
        # Sphere source
        self.sphereSource = vtk.vtkSphereSource()
        self.sphereSource.SetRadius(0.02)
        vtkPoints = vtk.vtkPoints()
        vtkPoints.SetData(numpy_to_vtk(currentGrid))
        sphereDataLoad = vtk.vtkPolyData()
        sphereDataLoad.SetPoints(vtkPoints)
        glyphLoad = vtk.vtkGlyph3D()
        glyphLoad.SetScaleModeToScaleByVector()
        glyphLoad.SetSourceConnection(self.sphereSource.GetOutputPort())
        glyphLoad.SetInputData(sphereDataLoad)
        glyphLoad.Update()
        sphereMapperLoad = vtk.vtkPolyDataMapper()
        sphereMapperLoad.SetInputConnection(glyphLoad.GetOutputPort())
        sphereActorLoads = vtk.vtkActor()
        sphereActorLoads.GetProperty().SetColor(1.0, 0., 0.)
        sphereActorLoads.SetMapper(sphereMapperLoad)

        # Sphere source
        self.sphereSource1 = vtk.vtkSphereSource()
        self.sphereSource1.SetRadius(0.02)
        vtkPoints1 = vtk.vtkPoints()
        vtkPoints1.SetData(numpy_to_vtk(myModel))
        #self.defineAxisLength(scaleFactor)
        sphereDataLoad1 = vtk.vtkPolyData()
        sphereDataLoad1.SetPoints(vtkPoints1)
        glyphLoad1 = vtk.vtkGlyph3D()
        glyphLoad1.SetScaleModeToScaleByVector()
        glyphLoad1.SetSourceConnection(self.sphereSource1.GetOutputPort())
        glyphLoad1.SetInputData(sphereDataLoad1)
        glyphLoad1.Update()
        sphereMapperLoad1 = vtk.vtkPolyDataMapper()
        sphereMapperLoad1.SetInputConnection(glyphLoad1.GetOutputPort())
        sphereActorLoads1 = vtk.vtkActor()
        sphereActorLoads1.GetProperty().SetColor(0.7, 0.7, 0.7)
        sphereActorLoads1.SetMapper(sphereMapperLoad1)
        window = vtk.vtkRenderWindow()
        # Sets the pixel width, length of the window.
        window.SetSize(500, 500)

        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(window)

        renderer = vtk.vtkRenderer()
        window.AddRenderer(renderer)

        renderer.AddActor(sphereActorLoads)
        renderer.AddActor(sphereActorLoads1)
        # Setting the background to blue.
        renderer.SetBackground(0.1, 0.1, 0.4)

        window.Render()
        interactor.Start()



        

