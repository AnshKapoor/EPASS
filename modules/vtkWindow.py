
import math
import numpy as np
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.numpy_support import numpy_to_vtk
from PyQt5.QtWidgets import QSizePolicy, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt
from standardWidgets import resetButton
from standardFunctionsGeneral import getVTKElem

class vtkWindow(QVTKRenderWindowInteractor):
    def __init__(self, parentWidget, ak3path, axisSelector = 1):
        super(vtkWindow, self).__init__(parentWidget)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        #self.scalar_bar_widget = None # needs to be initialized when actual 3D data is loaded (NEVER before import of data!!!)
        self.ak3path = ak3path

        # Empty lists are filled with model load by model class
        self.grids = []
        self.loadGrids = []
        self.mappers = []
        self.edgeMappers = []
        self.loadMappers = []
        self.actors = []
        self.edgeActors = []
        self.loadActors = []
        self.sphereActorLoads = []

        # Create Renderer
        self.ren = vtk.vtkRenderer()
        self.ren.UseFXAAOn()
        self.colors = vtk.vtkNamedColors()
        self.myBackgroundColors = [self.colors.GetColor3d('Black'), self.colors.GetColor3d('Grey'), self.colors.GetColor3d('White')]
        self.colorCounter = 0
        self.ren.SetBackground(self.myBackgroundColors[self.colorCounter])
        self.GetRenderWindow().AddRenderer(self.ren)

        # Create Interactor
        self.iren = self.GetRenderWindow().GetInteractor()
        self.irenStyle = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.irenStyle)

        # Axis
        self.mainAxes = vtk.vtkAxesActor()
        myAxes = [self.mainAxes.GetXAxisCaptionActor2D(), self.mainAxes.GetYAxisCaptionActor2D(), self.mainAxes.GetZAxisCaptionActor2D()]
        prop = vtk.vtkTextProperty()
        prop.SetFontSize(1)
        [axis.SetCaptionTextProperty(prop) for axis in myAxes]
        self.ren.AddActor(self.mainAxes)
        
        # Sphere source
        self.sphereSource = vtk.vtkSphereSource()
        self.sphereSource.SetRadius(0.02)
        
        # Lookup Table
        self.lut = vtk.vtkLookupTable()
        self.lut.SetNumberOfTableValues(200)
        [self.lut.SetTableValue(n, n/100., n/100., n/100., 1.0 ) for n in range(100)] # BW-Colormap
        [self.lut.SetTableValue(100+n, (100-n)/100., (100-n)/100., (100-n)/100., 1.0 ) for n in range(100)] # BW-Colormap
        self.lut.SetRampToLinear()
        self.lut.Build()
        
        # Lookup Table
        colorSeries = vtk.vtkColorSeries()
        colorSeries.SetColorScheme(vtk.vtkColorSeries.WARM)
        self.lutColor = vtk.vtkLookupTable()
        colorSeries.BuildLookupTable(self.lutColor, vtk.vtkColorSeries.ORDINAL)
        
        # Scalar bar
        self.scalarBar = vtk.vtkScalarBarActor()
        self.scalarBar.SetLookupTable(self.lut)
        self.scalarBar.SetWidth(0.02)
        self.scalarBar.UnconstrainedFontSizeOff()
        self.scalarBar.SetUnconstrainedFontSize(18)
        self.scalarBar.SetNumberOfLabels(10)
        self.scalarBarWidget = vtk.vtkScalarBarWidget()
        self.scalarBarWidget.SetScalarBarActor(self.scalarBar)
        self.scalarBarWidget.SetInteractor(self.iren)

        # 2D Text info on frequencyStep
        self.stepValueActor = vtk.vtkTextActor()
        self.stepValueActor.SetPosition(10, 10)
        self.stepValueActor.GetTextProperty().SetFontSize(24)
        self.stepValueActor.GetTextProperty().SetColor ( 0.7, 0.7, 0.7)
        self.stepValueActor.SetInput('-')
        self.ren.AddActor2D(self.stepValueActor)

        # CREATE WIDGETS | Init selection part
        self.axisSelector = QCheckBox('Axis')
        self.axisSelector.setCheckState(Qt.Checked)
        self.axisSelector.clicked.connect(self.axisChange)
        self.resetViewButton = resetButton()
        self.resetViewButton.clicked.connect(self.resetView)
        # ADD TO LAYOUT
        self.selectionLayout = QHBoxLayout()
        if axisSelector:
          self.selectionLayout.addWidget(self.axisSelector)
        self.selectionLayout.addStretch(1)
        self.selectionLayout.addWidget(self.resetViewButton)

        # Initialize
        self.iren.Initialize()
        self.iren.Start()

    def updateLoads(self, loads):
        blocksToDraw = []
        for n, load in enumerate(loads):
            for act in load.actorsList:
                state = load.drawCheck.isChecked()
                if state==0:
                    self.ren.RemoveActor(act)
                elif state==1:
                    self.ren.AddActor(act)
                    if load.superType == 'elemLoad':
                        for p, blockCheck in enumerate(load.blockChecker):
                            blockState = blockCheck.isChecked()
                            if blockState==1:
                                blocksToDraw.append(p)
            # Color blocks
            if load.superType == 'elemLoad':
                if not load.type == 'vn' and not load.type == 'freqVarDat':
                    blockCounter = 0
                    for block in range(len(load.blockChecker)):
                        if block in blocksToDraw:
                            noOfCells = self.grids[block].GetNumberOfCells()
                            for arNo in range(self.grids[block].GetCellData().GetNumberOfArrays()-1,-1,-1):
                                self.grids[block].GetCellData().RemoveArray(arNo)
                            phaseArray = numpy_to_vtk(load.surfacePhases[self.currentFrequencyStep, blockCounter:(blockCounter+noOfCells)])
                            phaseArray.SetName('Phase')
                            self.grids[block].GetCellData().AddArray(phaseArray)
                            self.mappers[block].SetLookupTable(self.lut)
                            self.mappers[block].ScalarVisibilityOn()
                            self.mappers[block].SetScalarModeToUseCellFieldData()
                            self.mappers[block].SelectColorArray('Phase')
                            self.mappers[block].SetScalarRange((0., 2*math.pi))
                            if blockCounter == 0:
                                self.ren.AddActor2D(self.scalarBar)
                            blockCounter = blockCounter + noOfCells
                        else:
                            self.mappers[block].ScalarVisibilityOff()
                            for arNo in range(self.grids[block].GetCellData().GetNumberOfArrays()-1,-1,-1):
                                self.grids[block].GetCellData().RemoveArray(arNo)
    
    def updateConstraints(self, constraints):
        for n, constraint in enumerate(constraints):
            for act in constraint.actorsList:
                state = constraint.drawCheck.isChecked()
                if state==0:
                    self.ren.RemoveActor(act)
                elif state==1:
                    self.ren.AddActor(act)
    
    def createGrid(self, nodes, nodesInv, elems):
        # Create the points based on nodes
        vtkPoints = vtk.vtkPoints()
        sortedNodeIdx = dict(sorted(nodesInv.items(), key=lambda item: item[0]))
        orderIdx = [item[1] for item in sortedNodeIdx.items()]
        vtkPoints.SetData(numpy_to_vtk(np.array([nodes[:]['xCoords'][orderIdx], nodes[:]['yCoords'][orderIdx], nodes[:]['zCoords'][orderIdx]]).T))
        nodesToVTK = dict([[x,n] for n,x in enumerate(nodes[:]['Ids'][orderIdx])])
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
        self.defineAxisLength(scaleFactor)
        sphereDataLoad = vtk.vtkPolyData()
        sphereDataLoad.SetPoints(vtkPoints)
        glyphLoad = vtk.vtkGlyph3D()
        glyphLoad.SetScaleModeToScaleByVector()
        glyphLoad.SetSourceConnection(self.sphereSource.GetOutputPort())
        glyphLoad.SetInputData(sphereDataLoad)
        glyphLoad.Update()
        sphereMapperLoad = vtk.vtkPolyDataMapper()
        sphereMapperLoad.SetInputConnection(glyphLoad.GetOutputPort())
        self.sphereActorLoads.append(vtk.vtkActor())
        self.sphereActorLoads[-1].GetProperty().SetColor(0.7, 0.7, 0.7)
        self.sphereActorLoads[-1].SetMapper(sphereMapperLoad)
        self.ren.AddActor(self.sphereActorLoads[-1])
        #
        # Create the elements
        blockGrids = []
        blockActors = []
        blockEdgeActors = []
        for block in elems:
          if block.shape[1]>3: # Exclude springs, points
            blockGrids.append(vtk.vtkUnstructuredGrid())
            blockGrids[-1].SetPoints(vtkPoints)
            vtkCells = vtk.vtkCellArray()
            newElem, newElemTypeId, nnodes = getVTKElem(block.attrs['ElementType'])
            cells = np.zeros((block.shape[0],nnodes+1), dtype=np.int64)
            cells[:,0] = nnodes
            for elemCount in range(block.shape[0]):
              cells[elemCount,1:] = [nodesToVTK[ID] for ID in block[elemCount,1:(nnodes+1)]]
            vtkCells.SetCells(block.shape[0], numpy_to_vtk(cells, deep = 1, array_type = vtk.vtkIdTypeArray().GetDataType()))
            blockGrids[-1].SetCells(newElemTypeId, vtkCells)
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputData(blockGrids[-1])
            blockActors.append(vtk.vtkActor())
            actor = blockActors[-1]
            actor.SetMapper(mapper)
            actor.GetProperty().SetAmbient(0.9)
            actor.GetProperty().SetDiffuse(0.1)
            actor.GetProperty().SetSpecular(0.)
            actor.GetProperty().SetOpacity(0.85)
            actor.GetProperty().SetColor(0.3,0.3,0.3)
            edgeMapper = vtk.vtkDataSetMapper()
            edgeMapper.SetInputData(blockGrids[-1])
            blockEdgeActors.append(vtk.vtkActor())
            edgeActor = blockEdgeActors[-1]
            edgeActor.SetMapper(edgeMapper)
            edgeActor.GetProperty().SetRepresentationToWireframe()
            edgeActor.GetProperty().SetLineWidth(3)
            edgeActor.GetProperty().SetColor(0.7,0.7,0.7)
            self.ren.AddActor(actor)
            self.ren.AddActor(edgeActor)
            # Add actor (show everything at beginning)
            #self.ren.AddActor(actor) for actor in [sphereActorLoad]]
        #
        return blockGrids, nodesToVTK, self.sphereActorLoads[-1], blockActors, blockEdgeActors
    
    def colorplot(self, myArray, field, grids, blockMappers, warp=0):
        vtkArray = numpy_to_vtk(myArray)
        vtkArray.SetName(field)
        if warp:
          print('Warp!')
        for n in range(len(grids)):
          grids[n].GetPointData().AddArray(vtkArray)
          blockMappers[n].SetLookupTable(self.lutColor)
          blockMappers[n].ScalarVisibilityOn()
          blockMappers[n].SetScalarModeToUsePointFieldData()
          blockMappers[n].SelectColorArray(field)
          blockMappers[n].SetScalarRange((min(myArray), max(myArray)))
        self.scalarBar.SetLookupTable(self.lutColor)
        self.ren.AddActor(self.scalarBar)
        self.GetRenderWindow().Render()
        
    def updateWindow(self, myModel):
        for blockIdx in range(myModel.blockInfo.rowCount()):
            state = myModel.blockInfo.item(blockIdx,0).checkState()
            if state==0:
                self.ren.RemoveActor(self.actors[blockIdx])
                self.ren.RemoveActor(self.edgeActors[blockIdx])
            elif state==2:
                self.ren.AddActor(self.actors[blockIdx])
                self.ren.AddActor(self.edgeActors[blockIdx])
        self.ren.RemoveActor(self.scalarBar)
        self.updateLoads(myModel.loads)
        self.updateConstraints(myModel.constraints)
        self.stepValueActor.SetInput(str(myModel.frequencies[self.currentFrequencyStep]) + ' Hz')
        self.GetRenderWindow().Render()
    
    def updateNumber(self):
        self.stepValueActor.SetInput(str(round(self.currentFrequency,2)) + ' Hz')
        self.GetRenderWindow().Render()
    
    def defineAxisLength(self, scaleFactor):
        self.mainAxes.SetTotalLength(scaleFactor*0.5,scaleFactor*0.5,scaleFactor*0.5)
    
    def axisChange(self):
        if self.axisSelector.checkState() == 2:
            self.ren.AddActor(self.mainAxes)
        elif self.axisSelector.checkState() == 0:
            self.ren.RemoveActor(self.mainAxes)
        self.GetRenderWindow().Render()

    def axisEnable(self):
        self.ren.AddActor(self.mainAxes)
        self.GetRenderWindow().Render()
    
    def axisDisable(self):
        self.ren.RemoveActor(self.mainAxes)
        self.GetRenderWindow().Render()
    
    def nodesEnable(self):
        [self.ren.AddActor(actor) for actor in self.sphereActorLoads]
        self.GetRenderWindow().Render()
    
    def nodesDisable(self):
        [self.ren.RemoveActor(actor) for actor in self.sphereActorLoads]
        self.GetRenderWindow().Render()
        
    def changeBackgroundColor(self):
        self.colorCounter = self.colorCounter + 1
        if self.colorCounter > len(self.myBackgroundColors)-1: 
          self.colorCounter = 0
        self.ren.SetBackground(self.myBackgroundColors[self.colorCounter])
        self.GetRenderWindow().Render()
    
    def warpEnable(self):
        #self.ren.AddActor(self.mainAxes)
        self.GetRenderWindow().Render()
    
    def warpDisable(self):
        #self.ren.RemoveActor(self.mainAxes)
        self.GetRenderWindow().Render()

    def resetView(self):
        self.ren.ResetCamera()
        self.GetRenderWindow().Render()

    def clearWindow(self):
        self.ren.RemoveAllViewProps()
        if self.axisSelector.checkState() == 2:
            self.ren.AddActor(self.mainAxes)
        self.ren.AddActor2D(self.stepValueActor)
        self.ren.AddActor2D(self.scalarBar)
        self.ren.ResetCamera()
        self.GetRenderWindow().Render()
