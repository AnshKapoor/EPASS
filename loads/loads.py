#
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy
import numpy as np
import math

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
        [self.contLayout.addLayout(load) for load in loads]
        self.contLayout.addStretch(1)
        self.update()

# General load class
class load(QHBoxLayout):
    def __init__(self):
        super(load, self).__init__()

    # Find one point per element at which pressure shall be generated
    def findRelevantPoints(self):
        self.surfacePoints = []
        self.surfaceElements = []
        self.surfaceElementNormals = []
        relevantBlocks = []
        nodes = self.myModel.calculationObjects[0].nodes
        for p, blockCheck in enumerate(self.blockChecker):
            blockState = blockCheck.isChecked()
            if blockState==1:
                relevantBlocks.append(self.myModel.calculationObjects[0].elems[p][1])
        for elems in self.myModel.calculationObjects[0].elems:
            if elems[1] in relevantBlocks:
                for elem in elems[2]:
                    elemID = elem[0]
                    node1 = nodes[nodes[:,0]==elem[1]][0]
                    node2 = nodes[nodes[:,0]==elem[2]][0]
                    node3 = nodes[nodes[:,0]==elem[3]][0]
                    node4 = nodes[nodes[:,0]==elem[4]][0]
                    centerX = 0.25*(node1[1]+node2[1]+node3[1]+node4[1])
                    centerY = 0.25*(node1[2]+node2[2]+node3[2]+node4[2])
                    centerZ = 0.25*(node1[3]+node2[3]+node3[3]+node4[3])
                    self.surfacePoints.append([centerX, centerY, centerZ])
                    self.surfaceElements.append(elemID)
                    vec1 = [ node1[1]-centerX, node1[2]-centerY, node1[3]-centerZ ] # from center to node 1
                    vec2 = [ node2[1]-centerX, node2[2]-centerY, node2[3]-centerZ ] # from center to node 2
                    vec3 = [ node3[1]-centerX, node3[2]-centerY, node3[3]-centerZ ] # from center to node 3
                    vec4 = [ node4[1]-centerX, node4[2]-centerY, node4[3]-centerZ ] # from center to node 4
                    elemNormal = 0.5 * (np.cross(vec1, vec2) + np.cross(vec3, vec4)) # Mean value of two normal vectors
                    elemNormal = elemNormal / np.linalg.norm(elemNormal)
                    loadNormal = [float(self.dirX.text()), float(self.dirY.text()), float(self.dirZ.text())]
                    loadNormal = loadNormal/np.linalg.norm(loadNormal)
                    angle = np.arccos(np.dot(loadNormal, elemNormal) / (np.linalg.norm(loadNormal) * np.linalg.norm(elemNormal)))*180./math.pi
                    if angle>90.:
                        self.surfaceElementNormals.append(-1*elemNormal)
                    else:
                        self.surfaceElementNormals.append(elemNormal)
