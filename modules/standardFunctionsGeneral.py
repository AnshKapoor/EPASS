#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
import numpy as np
import os
from PyQt5.QtWidgets import QApplication
from standardWidgets import progressWindow

# Read Nodes from ak3, ID and coord are available in calculationObject.nodes after this call
def readNodes(calculationObject, ak3tree):
    #YET TO BE CHANGED FOR BINARY FILE#
    nodeCount = int(ak3tree.find('Nodes').get('N')) # count nodes
    nodesTree = ak3tree.find('Nodes').findall('Node') # get each node
    calculationObject.nodes = np.zeros((nodeCount,4)) # prepare matrix for nodes
    progWin = progressWindow(nodeCount-1, 'Reading nodes')
    for n, oneNode in enumerate(nodesTree):
        calculationObject.nodes[n,0] = int(oneNode.find('Id').text) # get node's IDs
        calculationObject.nodes[n,1] = float(oneNode.find('x').text) # get node's x-Coords
        calculationObject.nodes[n,2] = float(oneNode.find('y').text) # get node's y-Coords
        calculationObject.nodes[n,3] = float(oneNode.find('z').text) # get node's z-Coords
        progWin.setValue(n+1)
        QApplication.processEvents()

def readNodesNew(calculationObject, binFile):
    #binFile = self.myModel.binFile
    nodesList = binFile.get('nodesSet/n0')
    nodeCount = len(nodesList)
    calculationObject.nodes = (np.array(nodesList)).tolist()
    QApplication.processEvents()



# Read Elements block-wise from ak3, ID and nodes are available in calculationObject.elems after this call
def readElems(calculationObject, ak3tree):
    #YET TO BE CHANGED FOR BINARY FILE#
    for elementGroup in ak3tree.findall('Elements'):
        no_of_nodes = 0
        info = []
        elem_type = 'none'
        elems_dom = None
        if not elems_dom:
            elems_dom = elementGroup.find('DSG4')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('DSG4')
                elem_type = 'DSG4'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 4:
                    no_of_nodes = 4
                info.append('                              '+str(elem_count)+' DSG4 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('DSG9')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('DSG9')
                elem_type = 'DSG9'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 9:
                    no_of_nodes = 9
                info.append('                              '+str(elem_count)+' DSG9 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Disc9')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Disc9')
                elem_type = 'Disc9'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 9:
                    no_of_nodes = 9
                info.append('                              '+str(elem_count)+' Disc9 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Kirch4')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Kirch4')
                elem_type = 'Kirch4'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 4:
                    no_of_nodes = 4
                info.append('                              '+str(elem_count)+' Kirch4 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('PlShell4')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('PlShell4')
                elem_type = 'PlShell4'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 4:
                    no_of_nodes = 4
                info.append('                              '+str(elem_count)+' PlShell4 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('PlShell9')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('PlShell9')
                elem_type = 'PlShell9'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 9:
                    no_of_nodes = 9
                info.append('                              '+str(elem_count)+' PlShell9 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Fluid27')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Fluid27')
                elem_type = 'Fluid27'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 27:
                    no_of_nodes = 27
                info.append('                              '+str(elem_count)+' Fluid27 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Fluid8')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Fluid8')
                elem_type = 'Fluid8'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 8:
                    no_of_nodes = 8
                info.append('                              '+str(elem_count)+' Fluid8 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Brick27')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Brick27')
                elem_type = 'Brick27'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 27:
                    no_of_nodes = 27
                info.append('                              '+str(elem_count)+' Brick27 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Brick20')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Brick20')
                elem_type = 'Brick20'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 20:
                    no_of_nodes = 20
                info.append('                              '+str(elem_count)+' Brick20 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Brick8')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Brick8')
                elem_type = 'Brick8'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 8:
                    no_of_nodes = 8
                info.append('                              '+str(elem_count)+' Brick8 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elems_dom = elementGroup.find('Tetra10')
            if elems_dom is not None:
                elems_dom = elementGroup.findall('Tetra10')
                elem_type = 'Tetra10'
                elem_count = int(elementGroup.get('N')) # count elements
                if no_of_nodes <= 10:
                    no_of_nodes = 10
                info.append('                              '+str(elem_count)+' Tetra10 elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is None:
            elem_count = int(elementGroup.get('N')) # count elements
            info.append('                              '+str(elem_count)+' ignored elements (block '+str(elementGroup.get('GroupId'))+')')
        if elems_dom is not None:
            currElems = np.zeros((elem_count,no_of_nodes+1), dtype=np.int) # prepare matrix for elems
            currElems[:,0] = [int(oneElem.find('Id').text) for oneElem in elems_dom] # get all elements' IDs
            progWin = progressWindow(elem_count-1, 'Reading elements of block ' + elementGroup.get('GroupId'))
            for i in range(len(elems_dom)):
                oneElem = elems_dom[i]
                currElems[i,1:no_of_nodes+1] = [int(oneNode.text) for oneNode in oneElem.findall('N')] # get all element information
                progWin.setValue(i+1)
                QApplication.processEvents()
            calculationObject.elems.append([elem_type, elementGroup.get('GroupId'), currElems])
    return info

# Read frequencies from ak3 file
def readFreqs(myModel):
    if os.path.exists(myModel.path + '/' + myModel.name + '.frq'):
        freqFile = open(myModel.path + '/' + myModel.name + '.frq', 'r')
        myModel.calculationObjects[-1].frequencies = [float(x) for x in freqFile]
        myModel.calculationObjects[-1].frequencyFile = 1
        freqFile.close()
    else:
        freq_start = float(myModel.ak3tree.find('Analysis').find('start').text)
        freq_steps = int(myModel.ak3tree.find('Analysis').find('steps').text)
        freq_delta = float(myModel.ak3tree.find('Analysis').find('delta').text)
        myModel.calculationObjects[-1].frequencyFile = 0
        myModel.calculationObjects[-1].frequencies = [freq_start+n*freq_delta for n in range(freq_steps)]
