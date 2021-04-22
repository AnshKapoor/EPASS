#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
import numpy as np
import os
from PyQt5.QtWidgets import QApplication
from standardWidgets import *
import h5py

# Read Nodes from cub5 and save them into hdf5 OR only read nodes directly from hdf5
def readNodes(myModel, hdf5File, cub5File=0):
    if cub5File: 
        # Nodes 
        nodeIDs = cub5File['Mesh/Nodes/Node IDs']
        g = hdf5File.create_group('Nodes')
        comp_type = np.dtype([('Ids', 'i8'), ('xCoords', 'f8'), ('yCoords', 'f8'), ('zCoords', 'f8')])
        dataSet = g.create_dataset('mtxFemNodes', (len(nodeIDs),), comp_type)
        dataSet[:,'Ids'] = np.array(cub5File['Mesh/Nodes/Node IDs'][()], dtype=np.uint64)
        dataSet[:,'xCoords'] = cub5File['Mesh/Nodes/X Coords'][()]
        dataSet[:,'yCoords'] = cub5File['Mesh/Nodes/Y Coords'][()]
        dataSet[:,'zCoords'] = cub5File['Mesh/Nodes/Z Coords'][()]
        # Nodesets 
        g = hdf5File.create_group('Nodesets')
        if 'Nodesets' in cub5File['Simulation Model'].keys(): # If nodesets exist in cub5 file by coreform, then read them
            for nodeset in cub5File['Simulation Model/Nodesets'].keys():
                nodesetID = cub5File['Simulation Model/Nodesets/' + nodeset].attrs['nodeset_id'][()][0]
                g.create_dataset('vecNodeset' + str(nodesetID), data=cub5File['Simulation Model/Nodesets/' + nodeset + '/member ids'][()])
                g['vecNodeset' + str(nodesetID)].attrs['Id'] = np.uint64(nodesetID)
    # Standard ops/assignments
    myModel.nodes = hdf5File['Nodes/mtxFemNodes']
    for nodeset in hdf5File['Nodesets'].keys():
        myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])

# Read Elements from cub5 and save them into hdf5 OR only read elements directly from hdf5
def readElements(myModel, hdf5File, cub5File=0):
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
            myModel.elems.append(dataSet)
        # Element-/Sidesets 
        g = hdf5File.create_group('Elementsets')
        if 'Sidesets' in cub5File['Simulation Model'].keys(): # If sidesets exist in cub5 file by coreform, then read them as element sets
            for elemset in cub5File['Simulation Model/Sidesets'].keys():
                elemsetID = cub5File['Simulation Model/Sidesets/' + elemset].attrs['sideset_id'][()][0]
                g.create_dataset('vecElemset' + str(elemsetID), data=cub5File['Simulation Model/Sidesets/' + elemset + '/member ids'][()])
                g['vecElemset' + str(elemsetID)].attrs['Id'] = np.uint64(elemsetID)
    else: 
        for block in hdf5File['Elements'].keys():
            myModel.elems.append(hdf5File['Elements/' + block])
    for elemset in hdf5File['Elementsets'].keys():
        myModel.elementSets.append(hdf5File['Elementsets/' + elemset])

def identifyElemType(elemType): 
    if elemType[0] == 22: # Shell9
        return 'QUAD_9', 'PlShell9', 10;
    else:
        return 'notSupported'

def createInitialBlockDataSet(group, elemType, groupID, totalElems, nodesPerElem):
    elemData = np.zeros((totalElems, nodesPerElem), dtype=np.uint64)
    dataSet = group.create_dataset('mtxFemElemGroup' + str(groupID), data=elemData)
    dataSet.attrs['ElementType'] = elemType
    dataSet.attrs['Id'] = np.uint64(groupID)
    dataSet.attrs['MaterialId'] = np.uint64(1)
    dataSet.attrs['MethodType'] = 'FEM'
    dataSet.attrs['N'] = np.uint64(totalElems)
    dataSet.attrs['Name'] = 'Block_' + str(groupID)
    dataSet.attrs['Orientation'] = 'global'
    dataSet.attrs['OrientationFile'] = ''
    return dataSet

# Read setup from hdf5 file
def readSetup(myModel, hdf5File, cub5File=0):
    if cub5File: 
        # Write standard values to hdf5 file
        g = hdf5File.create_group('Analysis')
        g.attrs['id'] = np.uint64(myModel.analysisID)
        g.attrs['type'] = myModel.analysisType 
        g.attrs['start'] = np.float64(myModel.freqStart)
        g.attrs['steps'] = np.uint64(myModel.freqSteps)
        g.attrs['delta'] = np.float64(myModel.freqDelta)
        g.attrs['solver'] = myModel.solverType
        g.attrs['revision'] = np.uint64(myModel.revision)
        g.attrs['description'] = myModel.description
    else:
        g = hdf5File['Analysis']
        myModel.analysisID = g.attrs['id'][()]
        myModel.analysisType = g.attrs['type'][:]
        myModel.freqStart = g.attrs['start'][()]
        myModel.freqSteps = g.attrs['steps'][()]
        myModel.freqDelta = g.attrs['delta'][()]
        myModel.solverType = g.attrs['solver'][:]
        myModel.revision = g.attrs['revision'][()]
        myModel.description = g.attrs['description'][:]
        myModel.frequencies = np.array([myModel.freqStart+n*myModel.freqDelta for n in range(myModel.freqSteps)])

# Read Elements block-wise from ak3, ID and nodes are available in calculationObject.elems after this call
# def readElements2(calculationObject, ak3tree):
    # #YET TO BE CHANGED FOR BINARY FILE#
    # for elementGroup in ak3tree.findall('Elements'):
        # no_of_nodes = 0
        # info = []
        # elem_type = 'none'
        # elems_dom = None
        # if not elems_dom:
            # elems_dom = elementGroup.find('DSG4')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('DSG4')
                # elem_type = 'DSG4'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 4:
                    # no_of_nodes = 4
                # info.append('                              '+str(elem_count)+' DSG4 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('DSG9')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('DSG9')
                # elem_type = 'DSG9'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 9:
                    # no_of_nodes = 9
                # info.append('                              '+str(elem_count)+' DSG9 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Disc9')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Disc9')
                # elem_type = 'Disc9'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 9:
                    # no_of_nodes = 9
                # info.append('                              '+str(elem_count)+' Disc9 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Kirch4')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Kirch4')
                # elem_type = 'Kirch4'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 4:
                    # no_of_nodes = 4
                # info.append('                              '+str(elem_count)+' Kirch4 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('PlShell4')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('PlShell4')
                # elem_type = 'PlShell4'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 4:
                    # no_of_nodes = 4
                # info.append('                              '+str(elem_count)+' PlShell4 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('PlShell9')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('PlShell9')
                # elem_type = 'PlShell9'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 9:
                    # no_of_nodes = 9
                # info.append('                              '+str(elem_count)+' PlShell9 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Fluid27')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Fluid27')
                # elem_type = 'Fluid27'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 27:
                    # no_of_nodes = 27
                # info.append('                              '+str(elem_count)+' Fluid27 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Fluid8')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Fluid8')
                # elem_type = 'Fluid8'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 8:
                    # no_of_nodes = 8
                # info.append('                              '+str(elem_count)+' Fluid8 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Brick27')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Brick27')
                # elem_type = 'Brick27'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 27:
                    # no_of_nodes = 27
                # info.append('                              '+str(elem_count)+' Brick27 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Brick20')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Brick20')
                # elem_type = 'Brick20'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 20:
                    # no_of_nodes = 20
                # info.append('                              '+str(elem_count)+' Brick20 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Brick8')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Brick8')
                # elem_type = 'Brick8'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 8:
                    # no_of_nodes = 8
                # info.append('                              '+str(elem_count)+' Brick8 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elems_dom = elementGroup.find('Tetra10')
            # if elems_dom is not None:
                # elems_dom = elementGroup.findall('Tetra10')
                # elem_type = 'Tetra10'
                # elem_count = int(elementGroup.get('N')) # count elements
                # if no_of_nodes <= 10:
                    # no_of_nodes = 10
                # info.append('                              '+str(elem_count)+' Tetra10 elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is None:
            # elem_count = int(elementGroup.get('N')) # count elements
            # info.append('                              '+str(elem_count)+' ignored elements (block '+str(elementGroup.get('GroupId'))+')')
        # if elems_dom is not None:
            # currElems = np.zeros((elem_count,no_of_nodes+1), dtype=np.int) # prepare matrix for elems
            # currElems[:,0] = [int(oneElem.find('Id').text) for oneElem in elems_dom] # get all elements' IDs
            # progWin = progressWindow(elem_count-1, 'Reading elements of block ' + elementGroup.get('GroupId'))
            # for i in range(len(elems_dom)):
                # oneElem = elems_dom[i]
                # currElems[i,0:no_of_nodes+1] = [int(oneNode.text) for oneNode in oneElem.findall('N')] # get all element information    change 0 to 1 for normal stuff! (so except for christophers ak3->hdf5 project)
                # progWin.setValue(i+1)
                # QApplication.processEvents()
            # calculationObject.elems.append([elem_type, elementGroup.get('GroupId'), currElems])
    # return info
