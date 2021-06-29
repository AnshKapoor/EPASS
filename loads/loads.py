#
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy
import numpy as np
import math
from standardWidgets import progressWindow
from standardFunctionsGeneral import getNodeIdxOfFaces

# ScrollArea containing loads in bottom left part of program
class loadInfoBox(QScrollArea):
    def __init__(self):
        super(loadInfoBox, self).__init__()
        self.setWidgetResizable(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Container widget for scroll area
        self.contWidget = QWidget()
        self.setWidget(self.contWidget)
        self.contLayout = QVBoxLayout(self.contWidget)

    # Clear all content in ScrollArea containing load info
    def clearLayout(self):
        ### Delete all layout content, if existing
        for i in reversed(range(self.contLayout.count())):
            if isinstance(self.contLayout.itemAt(i), QWidgetItem):
                self.contLayout.takeAt(i).widget().setParent(None)
            else:
                self.contLayout.removeItem(self.contLayout.takeAt(i))

    # Renew load content in ScrollArea
    def updateLayout(self, loads):
        self.clearLayout()
        [self.contLayout.addLayout(load) for load in loads]
        self.contLayout.addStretch(1)
        self.update()

# General elemLoad class
class elemLoad(QHBoxLayout):
    def __init__(self):
        super(elemLoad, self).__init__()
        self.superType = 'elemLoad'

    def calcLoadNormal(self, elemNormal):
        """
        calculates load normal and angle to element normals acc. to user input
        """
        loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
        loadNormal = loadNormal/np.linalg.norm(loadNormal)
        angle = np.arccos(np.dot(loadNormal, elemNormal) / (np.linalg.norm(loadNormal) * np.linalg.norm(elemNormal)))*180./math.pi
        if angle>90.:
            self.surfaceElementNormals.append(-1*elemNormal)
        else:
            self.surfaceElementNormals.append(elemNormal)

    def findRelevantPoints(self):
        """
        Find one point per element at which pressure shall be generated
        """
        self.surfacePoints = []
        self.surfaceElements = []
        self.surfaceElementNormals = []
        self.surfacePointsTest = []
        relevantBlocks = []
        nodes = self.myModel.nodes
        for p, blockCheck in enumerate(self.blockChecker):
            blockState = blockCheck.isChecked()
            if blockState==1:
                relevantBlocks.append(self.myModel.elems[p])
        for block in relevantBlocks:
            for elemIdx in range(block.attrs['N']):
                elemID = block[elemIdx,0]
                idx = self.myModel.nodesInv[block[elemIdx,1]]
                node1 = [nodes[idx]['xCoords'], nodes[idx]['yCoords'], nodes[idx]['zCoords']]
                idx = self.myModel.nodesInv[block[elemIdx,2]]
                node2 = [nodes[idx]['xCoords'], nodes[idx]['yCoords'], nodes[idx]['zCoords']]
                idx = self.myModel.nodesInv[block[elemIdx,3]]
                node3 = [nodes[idx]['xCoords'], nodes[idx]['yCoords'], nodes[idx]['zCoords']]
                idx = self.myModel.nodesInv[block[elemIdx,4]]
                node4 = [nodes[idx]['xCoords'], nodes[idx]['yCoords'], nodes[idx]['zCoords']]
                centerX = 0.25*(node1[0]+node2[0]+node3[0]+node4[0])
                centerY = 0.25*(node1[1]+node2[1]+node3[1]+node4[1])
                centerZ = 0.25*(node1[2]+node2[2]+node3[2]+node4[2])
                self.surfacePoints.append([centerX, centerY, centerZ])
                self.surfaceElements.append(elemID)
                vec1 = [ node1[0]-centerX, node1[1]-centerY, node1[2]-centerZ ] # from center to node 1
                vec2 = [ node2[0]-centerX, node2[1]-centerY, node2[2]-centerZ ] # from center to node 2
                vec3 = [ node3[0]-centerX, node3[1]-centerY, node3[2]-centerZ ] # from center to node 3
                vec4 = [ node4[0]-centerX, node4[1]-centerY, node4[2]-centerZ ] # from center to node 4
                elemNormal = 0.5 * (np.cross(vec1, vec2) + np.cross(vec3, vec4)) # Mean value of two normal vectors
                elemNormal = elemNormal / np.linalg.norm(elemNormal)
                try:
                    self.calcLoadNormal(elemNormal)
                except:
                    pass
        relevantBlocks = []
        nodes = 0
        
    def findRelevantFaces(self, plane, planeShift):
        """
        Find a face in selected plane
        """
        self.surfaceElements = []
        self.surfaceFaces = []
        self.surfaceFacesNormals = []
        self.surfacePoints = []
        relevantBlocks = []
        nodes = self.myModel.nodes
        for p, blockCheck in enumerate(self.blockChecker):
            blockState = blockCheck.isChecked()
            if blockState==1:
                relevantBlocks.append(self.myModel.elems[p])
        for block in relevantBlocks:
            nodeIdxOfFaces = getNodeIdxOfFaces(block.attrs['ElementType'])
            # Get sizes
            noOfFaces = nodeIdxOfFaces.shape[0]
            for elemIdx in range(block.attrs['N']):
                elem = block[elemIdx]
                for faceNo in range(noOfFaces): 
                    nodeIdx = [self.myModel.nodesInv[nodeID] for nodeID in elem[nodeIdxOfFaces[faceNo,:4]+1]] # indices of nodes belonging to the face
                    if np.all(np.abs(nodes[sorted(nodeIdx)][plane[0]+'Coords'] - planeShift) < 1e-6): # Check if all indices lie in chosen plane; Sorting necessary
                        self.surfaceElements.append(elem[0])
                        self.surfaceFaces.append(faceNo+1)
                        node1 = [nodes[nodeIdx[0]]['xCoords'], nodes[nodeIdx[0]]['yCoords'], nodes[nodeIdx[0]]['zCoords']]
                        node2 = [nodes[nodeIdx[1]]['xCoords'], nodes[nodeIdx[1]]['yCoords'], nodes[nodeIdx[1]]['zCoords']]
                        node3 = [nodes[nodeIdx[2]]['xCoords'], nodes[nodeIdx[2]]['yCoords'], nodes[nodeIdx[2]]['zCoords']]
                        node4 = [nodes[nodeIdx[3]]['xCoords'], nodes[nodeIdx[3]]['yCoords'], nodes[nodeIdx[3]]['zCoords']]
                        centerX = 0.25*(node1[0]+node2[0]+node3[0]+node4[0])
                        centerY = 0.25*(node1[1]+node2[1]+node3[1]+node4[1])
                        centerZ = 0.25*(node1[2]+node2[2]+node3[2]+node4[2])
                        self.surfacePoints.append([centerX, centerY, centerZ])
                        vec1 = [ node1[0]-centerX, node1[1]-centerY, node1[2]-centerZ ] # from center to node 1
                        vec2 = [ node2[0]-centerX, node2[1]-centerY, node2[2]-centerZ ] # from center to node 2
                        vec3 = [ node3[0]-centerX, node3[1]-centerY, node3[2]-centerZ ] # from center to node 3
                        vec4 = [ node4[0]-centerX, node4[1]-centerY, node4[2]-centerZ ] # from center to node 4
                        faceNormal = 0.5 * (np.cross(vec1, vec2) + np.cross(vec3, vec4)) # Mean value of two normal vectors
                        faceNormal = faceNormal / np.linalg.norm(faceNormal)
                        self.surfaceFacesNormals.append(faceNormal)
        relevantBlocks = []
        nodes = 0

    def nearestNeighbor(self):
        """
        finds next elements to given data points, writes into a proximity list, which can then be applied to the elements list
        """
        self.euclNearest = []
        for m, surfPoint in enumerate(np.array(self.surfacePoints)):
            # Calculates dist to each loaded dataPoint and saves the index of the  nearest dataPoint
            self.euclNearest.append(np.argmin([np.sum(np.square(dataPoint - surfPoint)) for n, dataPoint in enumerate(np.array(self.dataPoints))]))

    def switch(self):
        """
        Method changing the objects changedSwitch in order to indicate 2D and 3D update
        """
        if self.changeSwitch.isChecked():
            self.changeSwitch.setChecked(0)
        else:
            self.changeSwitch.setChecked(1)
                
    def data2hdf5(self, elemLoadsGroup):
        # Exporting the load per element
        progWin = progressWindow(len(self.surfaceElements)-1, 'Exporting ' + self.type + ' load ' + str(self.removeButton.id+1))
        for nE, surfaceElem in enumerate(self.surfaceElements):
            if not self.type == 'vn':
              frequencies = self.myModel.frequencies
              dataArray = [[frequencies[nf], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][0], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][1], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][2], self.surfacePhases[nf,nE]] for nf in range(len(frequencies))]
              dataSet = elemLoadsGroup.create_dataset('mtxFemElemLoad'+str(self.removeButton.id+1) + '_' + str(int(surfaceElem)), data=(dataArray))
              dataSet.attrs['FreqCount'] = np.uint64(len(frequencies))
            else:
              dataSet = elemLoadsGroup.create_dataset('mtxFemElemLoad'+str(self.removeButton.id+1) + '_' + str(int(surfaceElem)), data=[])
              dataSet.attrs['Face'] = np.uint64(self.surfaceFaces[nE]) # Assign element load to element
              dataSet.attrs['vn'] = np.float(self.amp.text()) # Assign element load to element
              dataSet.attrs['FreqCount'] = np.uint64(0)
            dataSet.attrs['Id'] = np.uint64(str(self.removeButton.id+1) + str(surfaceElem))
            dataSet.attrs['ElementId'] = np.uint64(surfaceElem) # Assign element load to element
            dataSet.attrs['LoadType'] = self.type
            dataSet.attrs['MethodType'] = 'FEM'
            # Update progress window
            progWin.setValue(nE)
            QApplication.processEvents()

# General elemLoad class
class nodeLoad(QHBoxLayout):
    def __init__(self):
        super(nodeLoad, self).__init__()
        self.superType = 'nodeLoad'
    
    def findRelevantPoints(self):
        """
        Extracts node points from selected nodesets
        """
        self.nodePoints = []
        self.nodePointsIds = []
        relevantNodesets = []
        nodes = self.myModel.nodes
        for p, nodesetCheck in enumerate(self.nodesetChecker):
            nodesetState = nodesetCheck.isChecked()
            if nodesetState==1:
                relevantNodesets.append(self.myModel.nodeSets[p])
        for nodeset in relevantNodesets:
            for nodeIdx in range(len(nodeset[:])):
                self.nodePointsIds.append(nodeset[nodeIdx][0])
                idx = (nodes[:]['Ids']==self.nodePointsIds[-1])
                self.nodePoints.append([nodes[idx]['xCoords'][0], nodes[idx]['yCoords'][0], nodes[idx]['zCoords'][0]])
            self.nodePoints = np.array(self.nodePoints)
        relevantNodesets = []
        nodes = 0
    
    def switch(self):
        """
        Method changing the objects changedSwitch in order to indicate 2D and 3D update
        """
        if self.changeSwitch.isChecked():
            self.changeSwitch.setChecked(0)
        else:
            self.changeSwitch.setChecked(1)
                
    def data2hdf5(self, nodeLoadsGroup):
        # Exporting the load per node
        progWin = progressWindow(len(self.nodePointsIds)-1, 'Exporting ' + self.type + ' load ' + str(self.removeButton.id+1))
        for nN, nodeId in enumerate(self.nodePointsIds):
            #frequencies = self.myModel.frequencies
            #dataArray = [[frequencies[nf], float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text()), 0.] for nf in range(len(frequencies))]
            #set = nodeLoadsGroup.create_dataset('mtxFemNodeLoad'+str(self.removeButton.id+1) + '_' + str(int(nodeId)), data=(dataArray))
            dataSet = nodeLoadsGroup.create_dataset('mtxFemNodeLoad'+str(self.removeButton.id+1) + '_' + str(int(nodeId)), data=[])
            #set.attrs['FreqCount'] = np.uint64(len(frequencies))
            dataSet.attrs['Id'] = np.uint64(str(self.removeButton.id+1) + str(nodeId))
            dataSet.attrs['NodeId'] = np.uint64(nodeId) # Assign element load to element
            dataSet.attrs['LoadType'] = self.type
            dataSet.attrs['MethodType'] = 'FEM'
            #
            dataSet.attrs['Fx'] = float(self.dirX.text())
            dataSet.attrs['Fy'] = float(self.dirY.text())
            dataSet.attrs['Fz'] = float(self.dirZ.text())
            # Update progress window
            progWin.setValue(nN)
            QApplication.processEvents()