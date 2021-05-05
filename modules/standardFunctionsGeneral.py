#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
import numpy as np
import vtk

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
            if coreformKey != 'notSupported':
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

def identifyElemType(elemType): 
    if elemType[0] == 22: # Quadrilateral with 9 nodes
        return 'QUAD_9', 'PlShell9', 10;
    elif elemType[0] == 43: # Hexahedron with 27 nodes
        return 'HEX_NODE_27', 'Fluid27', 28; 
    else:
        return 'notSupported', [], 0;

def identifyAlternativeElemTypes(elemType):
    if elemType in ['PlShell9','PlShell9pre','DSG9','Disc9','Fluid2d9']: 
        return ['PlShell9','PlShell9pre','DSG9','Disc9','Fluid2d9'];
    elif elemType in ['Fluid27','Brick27']:
        return ['Fluid27','Brick27'];
    else:
        return [];

def getPossibleInterfacePartner(elemType):
    if elemType in ['PlShell9', 'PlShell9pre','DSG9']:
        return ['Fluid27']
    elif elemType in ['Fluid27']:
        return ['PlShell9', 'PlShell9pre','DSG9']
    else:
        return []

def getVTKElem(elpasoElemType):
    if elpasoElemType in ['DSG4','DSG9','PlShell4','PlShell9','PlShell9pre','Disc9','Fluid2d9']:
        return vtk.vtkQuad(), 4
    elif elpasoElemType in ['Fluid8','Fluid27','Brick8','Brick20','Brick27']:
        return vtk.vtkHexahedron(), 8

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

def searchInterfaceElems(nodes, elems, blockCombinations):
    for blockCombi in blockCombinations: 
        print(blockCombi)
    return 1
