#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
import numpy as np
import os
from PyQt5.QtWidgets import QApplication
from standardWidgets import progressWindow
import h5py
from lxml import etree


#append new childs to the lxml-tree. old ones with same name will be overwritten
def buildAk3Framework(ak3tree):
    root = ak3tree.getroot()
    newChildList = ['Nodes', 'Elements']
    for item in newChildList:
        if (root.find(item)) is not None:
            root.remove(root.find(item))
        newChild = etree.SubElement(root, item)
        newChild.text = '\n'
        newChild.tail = '\n'

def saveParameters(calculationObject, binFileName):
    with h5py.File(binFileName, 'r+') as binFile:
        #analysisList = binFile.get('Analysis')

        binFile.attrs.modify('3_Analysis',np.string_(calculationObject.analysisType))
        binFile.attrs.modify('2_Solver',np.string_(calculationObject.solver))
        binFile.attrs.create('4_Freq_start',str(calculationObject.freqStart))
        binFile.attrs.create('5_steps',str(calculationObject.freqSteps))
        binFile.attrs.create('6_delta',str(calculationObject.freqDelta))

def writeHdf5Child(childlist, binFileName):
    with h5py.File(binFileName, 'r+') as binFile:
        for c, child in enumerate(childlist):
            binFile.create_group('/'+child)

def deleteHdf5Child(childlist, binFileName):
    with h5py.File(binFileName, 'r+') as binFile:
        for c, child in enumerate(childlist):
            if binFile.get('/'+child) is not None:
                binFile.__delitem__('/'+child)

def readHdf5(calculationObject, binFileName, ak3tree, DataToLookUp): #Convention: Read Functions always need to have the same name as the group in the file!
    with h5py.File(binFileName, 'r+') as binFile:
        groups = list(binFile.keys())
        print(set(binFile.keys()))
        for item in groups:
            if item in DataToLookUp:
                globals()['read'+item.capitalize()](calculationObject, binFileName, ak3tree) #looks for a function with the corresponding name

# Read Nodes from cub5 and save them into hdf5 OR only read nodes directly from hdf5
def readNodes(calculationObject, hdf5File, cub5File=0):
    if cub5File: 
        nodeIDs = cub5File['Mesh/Nodes/Node IDs']
        nodeData = np.zeros((len(nodeIDs),4))
        g = hdf5File.create_group('Nodes')
        g.create_dataset('mtxFemNodes', data=nodeData)
        dataSet = g['mtxFemNodes']
        dataSet[:,0] = cub5File['Mesh/Nodes/Node IDs'][()]
        dataSet[:,1] = cub5File['Mesh/Nodes/X Coords'][()]
        dataSet[:,2] = cub5File['Mesh/Nodes/Y Coords'][()]
        dataSet[:,3] = cub5File['Mesh/Nodes/Z Coords'][()]
    calculationObject.nodes = hdf5File['Nodes/mtxFemNodes']

# Read Elements from cub5 and save them into hdf5 OR only read elements directly from hdf5
def readElements(calculationObject, hdf5File, cub5File=0):
    if cub5File: 
        g = hdf5File.create_group('Elements')
        for block in cub5File['Simulation Model/Blocks'].keys():
            groupID = cub5File['Simulation Model/Blocks/' + block].attrs['block_id'][()][0]
            elemType = cub5File['Simulation Model/Blocks/' + block].attrs['element_type'][()]
            coreformKey, elemType, M = identifyElemType(elemType)
            N = cub5File['Simulation Model/Blocks/' + block].attrs['num_members'][()][0]
            if elemType is not 'notSupported':
                dataSet = createInitialBlockDataSet(g, elemType, groupID, N, M)
                dataSet[:,0] = cub5File['Simulation Model/Blocks/' + block + '/member ids'][:].T
                elemIDs = cub5File['Mesh/Elements/' + coreformKey + '/Element IDs']
                idx = [np.where(elemIDs[:] == elemID)[0][0] for elemID in dataSet[:,0]]
                dataSet[:,1:] = cub5File['Mesh/Elements/' + coreformKey + '/Connectivity'][idx,:]
            #self.calculationObject.elems.append([elemType, groupID, np.array((2,2)])
    #calculationObject.elems.append(hdf5File['Nodes/mtxFemNodes'])

def identifyElemType(elemType): 
    if elemType[0] == 22: # Shell9
        return 'QUAD_9', 'PlShell9', 10;
    else:
        return 'notSupported'

def createInitialBlockDataSet(group, elemType, groupID, totalElems, nodesPerElem):
    elemData = np.zeros((totalElems, nodesPerElem), dtype=np.uint32)
    dataSet = group.create_dataset('mtxFemElemGroup' + str(groupID), data=elemData)
    dataSet.attrs['ElementType'] = elemType
    dataSet.attrs['Id'] = groupID
    dataSet.attrs['MaterialType'] = 1
    dataSet.attrs['MethodType'] = 'FEM'
    dataSet.attrs['N'] = totalElems
    dataSet.attrs['Name'] = 'Block_' + str(groupID)
    dataSet.attrs['Orientation'] = 'global'
    dataSet.attrs['OrientationFile'] = ''
    return dataSet

# Read Elements block-wise from ak3, ID and nodes are available in calculationObject.elems after this call
def readElements2(calculationObject, ak3tree):
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
                currElems[i,0:no_of_nodes+1] = [int(oneNode.text) for oneNode in oneElem.findall('N')] # get all element information    change 0 to 1 for normal stuff! (so except for christophers ak3->hdf5 project)
                progWin.setValue(i+1)
                QApplication.processEvents()
            calculationObject.elems.append([elem_type, elementGroup.get('GroupId'), currElems])
    return info


def readElementsNew(calculationObject, binFileName, ak3tree):
    with h5py.File(binFileName, 'r') as binFile:
        elemsList = binFile.get('elements')
        root = ak3tree.getroot()
        for i in range(len(elemsList.keys())):
            groupdat = elemsList.get('g'+str(i))
            elements = root.find('Elements')
            elem_type = groupdat.attrs['type']
            group_id = groupdat.attrs['groupNo']
            elements.set('N', str(len(groupdat)))
            elements.set('GroupId', str(group_id))

            for item in groupdat:
                elm = etree.SubElement(elements, str(elem_type))
                id = etree.SubElement(elm, 'Id')
                id.text = str(item[0])
                for node in item:
                    N = etree.SubElement(elm, 'N')
                    N.text = str(node)
                elm.tail = '\n'

            calculationObject.elems.append([elem_type, group_id, np.array(groupdat)])



# Read frequencies from ak3 file
def readFreqs(myModel):
    try:
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
    except:
        freq_start = 1
        freq_steps = 100
        freq_delta = 1
        myModel.calculationObjects[-1].frequencyFile = 0
        myModel.calculationObjects[-1].frequencies = [freq_start+n*freq_delta for n in range(freq_steps)]
