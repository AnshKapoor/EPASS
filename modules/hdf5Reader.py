import sys
import h5py
import numpy as np

class hdf5Reader():
    """
    contains all necessary tools to read an hdf5-file according to
    the needs of the running instance of 'loadcreator'.
    Load as:         with //binfile// as binFile:
                        do stuff
    myModel and the calculationObject need to be arguments in order to be able to save the
    loaded data.
    """
    def __init__(self, binFile, myModel, calculationObject):
        """
        initialising basic concepts
        """
        super(hdf5Reader, self).__init__()
        self.binFile = binFile
        self.myModel = myModel
        self.calculationObject = calculationObject
        self.groups = list(binFile.keys())
        method_list = [func for func in dir(self) if callable(getattr(self, func))]
        #call read-functions: #put DataToLookUp into calcobj
        self.readNodesNew()
        self.readElements()
        for item in self.groups:
            if item in self.calculationObject.LookUpTable:
                method = getattr(self, 'read'+item.capitalize())
                method()


    def readNodesNew(self):
        nodesList = self.binFile.get('Nodes/mtxFemNodes')
        nodeCount = len(nodesList)
        for i, nodeinfo in enumerate(np.array(nodesList)):
            #calculationObject.nodes = (np.array(nodesList)).tolist()
            self.calculationObject.nodes = np.array(nodesList)
        print(self.calculationObject.nodes)
            #QApplication.processEvents()

    def readElements(self):
        elemsList = self.binFile.get('Elements')
        #root = ak3tree.getroot()
        for i in range(len(elemsList.keys())):
            groupdat = elemsList.get('mtxFemElemGroup'+str(i+1))
            elem_type = groupdat.attrs['ElementType']
            group_id = groupdat.attrs['Id']

            self.calculationObject.elems.append([elem_type, group_id, np.array(groupdat)])
#Idee: Ganz allgemeines Lesen. def ReadSmthg und attr0 = ..., attr1 = ..., dataArray = ...
#dann braucht man nur eine Funktion. Datenstruktur muss dann aber immer gleich sein und die Struktur am Speicherort darauf zugeschnitten sein.
#in der Telko ansprechen!
