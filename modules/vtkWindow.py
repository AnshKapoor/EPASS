
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
    def __init__(self, parentWidget, ak3path):
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

        # Create Renderer
        self.ren = vtk.vtkRenderer()
        self.ren.UseFXAAOn()
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

        # Lookup Table
        self.lut = vtk.vtkLookupTable()
        self.lut.SetNumberOfTableValues(200)
        [self.lut.SetTableValue(n, n/100., n/100., n/100., 1.0 ) for n in range(100)] # BW-Colormap
        [self.lut.SetTableValue(100+n, (100-n)/100., (100-n)/100., (100-n)/100., 1.0 ) for n in range(100)] # BW-Colormap
        self.lut.SetRampToLinear()
        self.lut.Build()

        # Scalar bar
        self.scalarBar = vtk.vtkScalarBarActor()
        self.scalarBar.SetLookupTable(self.lut)
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
        self.resetViewButton = resetButton(self.ak3path)
        self.resetViewButton.clicked.connect(self.resetView)
        # ADD TO LAYOUT
        self.selectionLayout = QHBoxLayout()
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
        vtkPoints.SetData(numpy_to_vtk(np.array([nodes[:]['xCoords'], nodes[:]['yCoords'], nodes[:]['zCoords']]).T))
        sphereSource = vtk.vtkSphereSource()
        scaleFactor = max( [abs(max(nodes[:]['xCoords'])-min(nodes[:]['xCoords'])), abs(max(nodes[:]['yCoords'])-min(nodes[:]['yCoords'])), abs(max(nodes[:]['zCoords'])-min(nodes[:]['zCoords']))] )
        self.defineAxisLength(scaleFactor)
        sphereSource.SetRadius(scaleFactor*0.01)
        sphereDataLoad = vtk.vtkPolyData()
        sphereDataLoad.SetPoints(vtkPoints)
        glyphLoad = vtk.vtkGlyph3D()
        glyphLoad.SetScaleModeToScaleByVector()
        glyphLoad.SetSourceConnection(sphereSource.GetOutputPort())
        glyphLoad.SetInputData(sphereDataLoad)
        glyphLoad.Update()
        sphereMapperLoad = vtk.vtkPolyDataMapper()
        sphereMapperLoad.SetInputConnection(glyphLoad.GetOutputPort())
        sphereActorLoad = vtk.vtkActor()
        sphereActorLoad.GetProperty().SetColor(0.7, 0.7, 0.7)
        sphereActorLoad.SetMapper(sphereMapperLoad)
        self.ren.AddActor(sphereActorLoad)
        # Create the elements
        blockActors = []
        blockEdgeActors = []
        for block in elems:
          newGrid = vtk.vtkUnstructuredGrid()
          newGrid.SetPoints(vtkPoints)
          vtkCells = vtk.vtkCellArray()
          newElem, newElemTypeId, nnodes = getVTKElem(block.attrs['ElementType'])
          cells = np.zeros((block.shape[0],nnodes+1), dtype=np.int64)
          cells[:,0] = nnodes
          for elemCount in range(block.shape[0]):
              cells[elemCount,1:] = [nodesInv[ID] for ID in block[elemCount,1:(nnodes+1)]]
          vtkCells.SetCells(block.shape[0], numpy_to_vtk(cells, deep = 1, array_type = vtk.vtkIdTypeArray().GetDataType()))
          newGrid.SetCells(newElemTypeId, vtkCells)
          mapper = vtk.vtkDataSetMapper()
          mapper.SetInputData(newGrid)
          blockActors.append(vtk.vtkActor())
          actor = blockActors[-1]
          actor.SetMapper(mapper)
          actor.GetProperty().SetAmbient(0.9)
          actor.GetProperty().SetDiffuse(0.1)
          actor.GetProperty().SetSpecular(0.)
          actor.GetProperty().SetOpacity(0.85)
          actor.GetProperty().SetColor(0.3,0.3,0.3)
          edgeMapper = vtk.vtkDataSetMapper()
          edgeMapper.SetInputData(newGrid)
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
        
        return sphereActorLoad, blockActors, blockEdgeActors
        
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
