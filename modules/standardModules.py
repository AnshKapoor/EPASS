#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
from PyQt5.QtWidgets import QApplication, QDialog, QScrollArea, QWidget, QGroupBox, QFormLayout, QVBoxLayout, QDialogButtonBox
from PyQt5.QtCore import Qt
import numpy as np
import math
from standardWidgets import progressWindow

def calcMeanSquared(hdf5ResultsFileStateGroup, fieldIndices, nodes, nodesInv, orderIdx, startIdxPerNode, elemBlock, noOfNodesPerElem, derivative=0):
  dofIdxOfElemNodes = np.zeros((elemBlock.attrs['N'],noOfNodesPerElem), dtype=int)
  for elemIdx in range(elemBlock.attrs['N']):
    #elemID = block[elemIdx,0]
    for n, node in enumerate(elemBlock[elemIdx,1:noOfNodesPerElem+1]): # Saves the idx of according first dof of patch/element
      tempStartIdxOfNode = startIdxPerNode[orderIdx[node]]
      if tempStartIdxOfNode in fieldIndices:
        dofIdxOfElemNodes[elemIdx,n] = tempStartIdxOfNode 
      else:
        dofIdxOfElemNodes[elemIdx,n] = fieldIndices[np.argmax(fieldIndices>tempStartIdxOfNode)]
  noOfStateResults = len(hdf5ResultsFileStateGroup.keys())
  x = np.zeros((noOfStateResults), dtype=float)
  y = np.zeros((noOfStateResults), dtype=float)
  counter = 0
  if derivative==0:
    progWin = progressWindow(noOfStateResults-1, 'Calculating mean squared values')
  else:
    progWin = progressWindow(noOfStateResults-1, 'Calculating mean squared derivative of order ' + str(derivative))
  for item in hdf5ResultsFileStateGroup.attrs.items():
    x[counter] = float(item[1])
    dataSet = hdf5ResultsFileStateGroup['vecFemStep' + str(int(item[0][8:]))]
    dataSetComplex = dataSet['real'][:] + 1j*dataSet['imag'][:]
    if derivative>0:
      dataSetComplex = np.multiply((1j*2*math.pi*x[counter])**derivative, dataSetComplex)
    myArray = [np.mean(np.power(np.abs(dataSetComplex[sorted(dofIdxOfElemNodes[n,:])]), 2)) for n in range(elemBlock.attrs['N'])]
    y[counter] = np.mean(myArray)
    counter = counter + 1
    progWin.setValue(counter)
    QApplication.processEvents()
  idx = np.argsort(x)
  return x[idx], y[idx]

class setupRayleighWindow(QDialog):
    def __init__(self):
        super(QDialog, self).__init__()
        self.setWindowTitle('Setup | Sound power')
        #
        self.setAutoFillBackground(True) # color
        p = self.palette() # color
        p.setColor(self.backgroundRole(), Qt.white) # color
        self.setPalette(p) # color
        #
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # setup
        self.formGroupBox = QGroupBox()
        self.layout = QFormLayout()
        self.formGroupBox.setLayout(self.layout)
        # block selection
        self.contWidget = QWidget()
        self.formGroupBoxBlocks = QScrollArea()
        self.formGroupBoxBlocks.setWidget(self.contWidget)
        self.formGroupBoxBlocks.setWidgetResizable(True)
        self.formGroupBoxBlocks.setMaximumHeight(400)
        self.blockLayout = QVBoxLayout(self.contWidget)
        #
        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.formGroupBox)
        self.mainLayout.addWidget(self.formGroupBoxBlocks)
        self.mainLayout.addWidget(self.buttonBox)
        self.setLayout(self.mainLayout)

def calcSoundPower(hdf5ResultsFileStateGroup, fieldIndices, nodes, nodesInv, orderIdx, startIdxPerNode, elemBlock, speedOfSound, density):
  # Calculating distance matrix
  normalOfElems = np.zeros((elemBlock.attrs['N'],3))
  centerOfElems = np.zeros((elemBlock.attrs['N'],3))
  areaOfElems = np.zeros((elemBlock.attrs['N']))
  dofIdxOfPatchNodes = np.zeros((elemBlock.attrs['N'],4), dtype=int)
  progWin = progressWindow(elemBlock.attrs['N']-1, 'Calculating areas and normals of block ' + str(elemBlock.attrs['Id']))
  for elemIdx in range(elemBlock.attrs['N']):
    #elemID = block[elemIdx,0]
    for n, node in enumerate(elemBlock[elemIdx,1:5]): # Saves the idx of according first dof of patch/element
      tempStartIdxOfPatchNode = startIdxPerNode[orderIdx[node]]
      if tempStartIdxOfPatchNode in fieldIndices:
        dofIdxOfPatchNodes[elemIdx,n] = tempStartIdxOfPatchNode 
      else:
        dofIdxOfPatchNodes[elemIdx,n] = fieldIndices[np.argmax(fieldIndices>tempStartIdxOfPatchNode)]
    nodeIdx = [nodesInv[node] for node in elemBlock[elemIdx,1:5]]
    nodeCoords = np.zeros((len(nodeIdx), 3))
    nodeCoords[:, 0] = [nodes[idx]['xCoords'] for idx in nodeIdx]
    nodeCoords[:, 1] = [nodes[idx]['yCoords'] for idx in nodeIdx]
    nodeCoords[:, 2] = [nodes[idx]['zCoords'] for idx in nodeIdx]
    centerOfElem = np.array([np.mean(nodes[sorted(nodeIdx)]['xCoords']), np.mean(nodes[sorted(nodeIdx)]['yCoords']), np.mean(nodes[sorted(nodeIdx)]['zCoords'])])
    centerOfElems[elemIdx,:] = centerOfElem
    vec1 = nodeCoords[0,:]-centerOfElem
    vec2 = nodeCoords[1,:]-centerOfElem
    vec3 = nodeCoords[2,:]-centerOfElem
    vec4 = nodeCoords[3,:]-centerOfElem
    normalOfElem = 0.5 * (np.cross(vec1, vec2) + np.cross(vec3, vec4)) # Mean value of two normal vectors
    normalOfElems[elemIdx,:] = normalOfElem / np.linalg.norm(normalOfElem)
    vec1 = nodeCoords[1,:]-nodeCoords[0,:]
    vec2 = nodeCoords[3,:]-nodeCoords[0,:]
    vec3 = nodeCoords[1,:]-nodeCoords[2,:]
    vec4 = nodeCoords[3,:]-nodeCoords[2,:]
    areaOfElems[elemIdx] = 0.5 * (np.linalg.norm(np.cross(vec1,vec2)) + np.linalg.norm(np.cross(vec3,vec4)))
    progWin.setValue(elemIdx)
    QApplication.processEvents()
  #
  totalArea = np.sum(areaOfElems)
  noOfPatches = elemBlock.attrs['N']
  distMatrix = np.zeros((noOfPatches, noOfPatches))
  progWin = progressWindow(noOfPatches-1, 'Calculating distances between patches in block ' + str(elemBlock.attrs['Id']))
  for m in range(noOfPatches): # Loop for the creation of distance matrix for each calculation object
    distMatrix[m,:] = np.power( np.power(centerOfElems[m,0] - centerOfElems[:,0] + 0.0001*normalOfElems[:,0],2) + np.power(centerOfElems[m,1] - centerOfElems[:,1] + 0.0001*normalOfElems[:,1],2) + np.power(centerOfElems[m,2] - centerOfElems[:,2] + 0.0001*normalOfElems[:,2],2), 0.5)
    progWin.setValue(m)
    QApplication.processEvents()   
  Z_fac = 1j * density * areaOfElems / (2 * math.pi * distMatrix)  # Impedance matrix as factor for Rayleigh Calculation
  #
  noOfStateResults = len(hdf5ResultsFileStateGroup.keys())
  x = np.zeros((noOfStateResults), dtype=np.float)
  y1 = np.zeros((noOfStateResults), dtype=np.float)
  y2 = np.zeros((noOfStateResults), dtype=np.float)
  counter = 0
  progWin = progressWindow(noOfStateResults-1, 'Calculating sound power using Rayleigh integral')
  for item in hdf5ResultsFileStateGroup.attrs.items():
    x[counter] = float(item[1])
    omega = 2 * math.pi * float(item[1])
    k = omega / speedOfSound
    dataSet = hdf5ResultsFileStateGroup['vecFemStep' + str(int(item[0][8:]))]
    dataSetComplex = dataSet['real'][:] + 1j*dataSet['imag'][:]
    #
    effDispOfPatches = np.empty((noOfPatches), dtype=np.complex)
    effDispOfPatches = [np.mean(dataSetComplex[sorted(dofIdxOfPatchNodes[n,:])]) for n in range(noOfPatches)]
    effVelocityOfPatches = np.multiply( (1j*omega*1.4142135623730951), effDispOfPatches)
    #
    pressureOfPatches = np.dot((Z_fac * np.exp(-1j * k * distMatrix)) * omega, effVelocityOfPatches)
    matIntensity = (pressureOfPatches * effVelocityOfPatches.conjugate()).real
    matPower = matIntensity * areaOfElems
    totalPower = matPower.sum(axis=0)
    #
    meanSquaredVelocity = np.sum(np.power(np.abs(effVelocityOfPatches),2) * areaOfElems) / totalArea
    sigma = np.divide((totalPower / (density * speedOfSound * totalArea)), meanSquaredVelocity) # radiation efficiency
    #
    y1[counter] = totalPower
    y2[counter] = sigma
    counter = counter + 1
    progWin.setValue(counter)
    QApplication.processEvents()
  idx = np.argsort(x)
  return x[idx],y1[idx],y2[idx]