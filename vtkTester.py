import vtk
from numpy import random
import numpy as np
import math, cmath, random, time
np.random.seed(int(time.time()))
pi = math.pi
randomize = True





class VtkPointCloud:

    def __init__(self, zMin=-10.0, zMax=10.0, maxNumPoints=1e6):
        self.maxNumPoints = maxNumPoints
        self.vtkPolyData = vtk.vtkPolyData()
        self.clearPoints()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.vtkPolyData)
        mapper.SetColorModeToDefault()
        mapper.SetScalarRange(zMin, zMax)
        mapper.SetScalarVisibility(1)
        self.vtkActor = vtk.vtkActor()
        self.vtkActor.SetMapper(mapper)

    def addPoint(self, point):
        if self.vtkPoints.GetNumberOfPoints() < self.maxNumPoints:
            pointId = self.vtkPoints.InsertNextPoint(point[:])
            self.vtkDepth.InsertNextValue(point[2])
            self.vtkCells.InsertNextCell(1)
            self.vtkCells.InsertCellPoint(pointId)
        else:
            r = random.randint(0, self.maxNumPoints)
            self.vtkPoints.SetPoint(r, point[:])
        self.vtkCells.Modified()
        self.vtkPoints.Modified()
        self.vtkDepth.Modified()

    def clearPoints(self):
        self.vtkPoints = vtk.vtkPoints()
        self.vtkCells = vtk.vtkCellArray()
        self.vtkDepth = vtk.vtkDoubleArray()
        self.vtkDepth.SetName('DepthArray')
        self.vtkPolyData.SetPoints(self.vtkPoints)
        self.vtkPolyData.SetVerts(self.vtkCells)
        self.vtkPolyData.GetPointData().SetScalars(self.vtkDepth)
        self.vtkPolyData.GetPointData().SetActiveScalars('DepthArray')
####################################
samples = 500
normal = [0.,0.,1.]
R = 1000 # Radius
center = [0., 0., 0.] # Center of Semisphere

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
        points.append([R*x_rot, R*y_rot, R*z_rot])

sourcePoints = np.array(points)

##################################

pointCloud = VtkPointCloud()
for k in points:
    pointCloud.addPoint(k)
pointCloud.addPoint([0,0,0])
pointCloud.addPoint([0,0,0])
pointCloud.addPoint([0,0,0])
pointCloud.addPoint([0,0,0])

# Renderer
renderer = vtk.vtkRenderer()
renderer.AddActor(pointCloud.vtkActor)
renderer.SetBackground(.2, .3, .4)
renderer.ResetCamera()

# Render Window
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# Interactor
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Begin Interaction
renderWindow.Render()
renderWindowInteractor.Start()
