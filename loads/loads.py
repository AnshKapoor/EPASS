#
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QScrollArea, QWidget, QWidgetItem, QSizePolicy
import os
import numpy as np
import math
from lxml import etree
import h5py
from standardWidgets import progressWindow

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
                    try:
                        self.calcLoadNormal(elemNormal)
                    except:
                        pass


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


    def writeXML(self, exportAK3, exportbin, name, cluster):
        """
        saves loads into existing .ak3 and hdf5
        """
        with h5py.File(exportbin, 'r+') as binfile:
            #binfile = self.myModel.binFile
            if binfile.get('/ElemLoads') is not None:
                binfile.__delitem__('/ElemLoads')
            elemLoads = exportAK3.find('ElemLoads')
            oldNoOfLoads = elemLoads.get('N')
            elemLoads.set('N', str(int(oldNoOfLoads) + len(self.surfaceElements)))
            loadedElems = exportAK3.find('LoadedElems')
            # Create a directory for load dat files
            loadDir = '/'.join(self.myModel.path.split('/')[0:-1]) + '/' + name + '_' + self.type + '_load_' + str(self.removeButton.id+1)
            if not os.path.exists(loadDir):
                os.mkdir(loadDir)
            else: # Clean directory
                for filename in os.listdir(loadDir):
                    os.remove(loadDir + '/' + filename)
            # Save loads for each element
            progWin = progressWindow(len(self.surfaceElements)-1, 'Exporting ' + self.type + ' load ' + str(self.removeButton.id+1))
            for nE, surfaceElem in enumerate(self.surfaceElements):
                # One load per element
                newLoad = etree.Element('ElemLoad', Type='structurefrq')
                newLoad.tail = '\n'
                newLoadID = etree.Element('Id')
                newLoadID.text = str(self.removeButton.id+1) + str(surfaceElem) # The id is a concatanation by the load id and the elem id
                newLoad.append(newLoadID)
                newFile = etree.Element('File')
                if cluster == 1:
                    strhead = '../../'
                else:
                    strhead = '../'
                newFile.text = strhead + name + '_' + self.type + '_load_' + str(self.removeButton.id+1) + '/elemLoad' + newLoadID.text + '.dat'
                newLoad.append(newFile)
                elemLoads.append(newLoad)
                # Save one file per load
                frequencies = self.myModel.calculationObjects[0].frequencies
                f = open(loadDir + '/elemLoad' + str(newLoadID.text) + '.dat', 'w')
                f.write(str(len(frequencies)) + '\n')

                [f.write(str(frequencies[nf]) + ' ' + str(-1.*float(self.amp.text())*self.surfaceElementNormals[nE][0]) + ' ' + str(-1.*float(self.amp.text())*self.surfaceElementNormals[nE][1]) + ' ' + str(-1.*float(self.amp.text())*self.surfaceElementNormals[nE][2]) + ' ' + str(self.surfacePhases[nf,nE]) + '\n') for nf in range(len(frequencies))]
                f.close()

                # Apply load to element
                newLoadedElem = etree.Element('LoadedElem')
                newLoadedElem.tail = '\n'
                newElemID = etree.Element('Id')
                newElemID.text = str(surfaceElem) # Element ID
                newLoadedElem.append(newElemID)
                newLoadID = etree.Element('Load')
                newLoadID.text = str(self.removeButton.id+1) + str(surfaceElem) # Load ID
                newLoadedElem.append(newLoadID)
                loadedElems.append(newLoadedElem)
                ###same for h5py file:
                dataArray = [[frequencies[nf], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][0], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][1], -1.*float(self.amp.text())*self.surfaceElementNormals[nE][2], self.surfacePhases[nf,nE]] for nf in range(len(frequencies))]
                set = binfile.create_dataset('/ElemLoads/mtxFemElemLoad'+str(self.removeButton.id+1) + str(surfaceElem), data=(dataArray))
                set.attrs['FreqCount'] = len(frequencies)
                loadElDat = [int(surfaceElem),int(str(self.removeButton.id+1)+str(surfaceElem))]
                #binfile.create_dataset('/loads/loadedElems/le'+str(self.removeButton.id+1) + str(surfaceElem), data=(loadElDat)) ID! Das muss jetzt mit in die mtxFemElemLoad als Attribute.
                ###
                # Update progress window
                progWin.setValue(nE)
                QApplication.processEvents()
