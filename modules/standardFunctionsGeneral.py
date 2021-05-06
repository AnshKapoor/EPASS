#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
from PyQt5.QtWidgets import QApplication
import numpy as np
import vtk
from standardWidgets import progressWindow

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
        myModel.nodesInv = dict([[ID, n] for n, ID in enumerate(dataSet[:,'Ids'])])
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

def getNodeIdxOfFaces(elemType):
    if elemType in ['PlShell9','PlShell9pre','DSG9','Disc9','Fluid2d9']:
        return np.array([[0,1,2,3,4,5,6,7,8]]) # Face 0
    elif elemType in ['Fluid27','Brick27']:
        return np.array([[0,1,5,4,8,13,16,12,25],
                         [2,3,7,6,19,15,18,14,26],
                         [0,3,2,1,11,10,9,8,21],
                         [1,2,6,5,9,14,17,13,24],
                         [4,5,6,7,16,17,18,19,22],
                         [0,4,7,3,12,19,15,11,23]]) # Face 0,1,2,3,4,5
    else:
        return []

def getVTKElem(elpasoElemType):
    if elpasoElemType in ['DSG4','DSG9','PlShell4','PlShell9','PlShell9pre','Disc9','Fluid2d9']:
        return vtk.vtkQuad(), 9, 4
    elif elpasoElemType in ['Fluid8','Fluid27','Brick8','Brick20','Brick27']:
        return vtk.vtkHexahedron(), 12, 8

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

def searchInterfaceElems(nodes, nodesInv, elems, blockCombinations):
    for blockCombi in blockCombinations: 
        # change number of faces
        nodeIdxOfFaces1 = getNodeIdxOfFaces(elems[blockCombi[0]].attrs['ElementType'])
        nodeIdxOfFaces2 = getNodeIdxOfFaces(elems[blockCombi[1]].attrs['ElementType'])
        # Get sizes
        noOfElems1 = len(elems[blockCombi[0]])
        noOfElems2 = len(elems[blockCombi[1]])
        noOfFaces1 = nodeIdxOfFaces1.shape[0]
        noOfFaces2 = nodeIdxOfFaces2.shape[0]
        noOfTotalFaces1 = noOfElems1 * noOfFaces1
        noOfTotalFaces2 = noOfElems2 * noOfFaces2
        # Init arrays containing all coordinates
        elemAndFaceIDs1 = []
        elemAndFaceIDs2 = []
        xCoords1 = np.zeros((noOfTotalFaces1,4))
        yCoords1 = np.zeros((noOfTotalFaces1,4))
        zCoords1 = np.zeros((noOfTotalFaces1,4))
        xCoords2 = np.zeros((noOfTotalFaces2,4))
        yCoords2 = np.zeros((noOfTotalFaces2,4))
        zCoords2 = np.zeros((noOfTotalFaces2,4))
        # Loops to collect coordinates in block 1
        progWin = progressWindow(len(elems[blockCombi[0]])-1, 'Collecting coordinates of block' + str(elems[blockCombi[0]].attrs['Id']))
        for m, elem1 in enumerate(elems[blockCombi[0]]):
            for faceNo1 in range(noOfFaces1): 
                nodeIdx1 = [nodesInv[nodeID] for nodeID in elem1[nodeIdxOfFaces1[faceNo1,:4]+1]] # indices of nodes belonging to the face
                xCoords1[m*noOfFaces1 + faceNo1,:] = np.sort(nodes[sorted(nodeIdx1)]['xCoords'])
                yCoords1[m*noOfFaces1 + faceNo1,:] = np.sort(nodes[sorted(nodeIdx1)]['yCoords'])
                zCoords1[m*noOfFaces1 + faceNo1,:] = np.sort(nodes[sorted(nodeIdx1)]['zCoords'])
                elemAndFaceIDs1.append([m, faceNo1])
            progWin.setValue(m)
            QApplication.processEvents()
        # Loops to collect coordinates in block 2
        progWin = progressWindow(len(elems[blockCombi[1]])-1, 'Collecting coordinates of block' + str(elems[blockCombi[1]].attrs['Id']))
        for m, elem2 in enumerate(elems[blockCombi[1]]): 
            for faceNo2 in range(noOfFaces2):
                nodeIdx2 = [nodesInv[nodeID] for nodeID in elem2[nodeIdxOfFaces2[faceNo2,:4]+1]] # indices of nodes belonging to the face
                xCoords2[m*noOfFaces2 + faceNo2,:] = np.sort(nodes[sorted(nodeIdx2)]['xCoords'])
                yCoords2[m*noOfFaces2 + faceNo2,:] = np.sort(nodes[sorted(nodeIdx2)]['yCoords'])
                zCoords2[m*noOfFaces2 + faceNo2,:] = np.sort(nodes[sorted(nodeIdx2)]['zCoords'])
                elemAndFaceIDs2.append([m, faceNo2])
            progWin.setValue(m)
            QApplication.processEvents()
        # Find interface elements for coincident nodes using saved coordinates
        progWin = progressWindow(noOfTotalFaces1-1, 'Searching interfaces between block' + str(elems[blockCombi[0]].attrs['Id']) + ' and ' + str(elems[blockCombi[1]].attrs['Id']))
        for m in range(noOfTotalFaces1):
            xIdx = ((xCoords2[:,0] == xCoords1[m,0]) & (xCoords2[:,1] == xCoords1[m,1]) & (xCoords2[:,2] == xCoords1[m,2]) & (xCoords2[:,3] == xCoords1[m,3]))
            yIdx = ((yCoords2[:,0] == yCoords1[m,0]) & (yCoords2[:,1] == yCoords1[m,1]) & (yCoords2[:,2] == yCoords1[m,2]) & (yCoords2[:,3] == yCoords1[m,3]))
            zIdx = ((zCoords2[:,0] == zCoords1[m,0]) & (zCoords2[:,1] == zCoords1[m,1]) & (zCoords2[:,2] == zCoords1[m,2]) & (zCoords2[:,3] == zCoords1[m,3]))
            idx = (xIdx & yIdx & zIdx).nonzero()[0][0]
            print('Elem ' + str(elemAndFaceIDs1[m][0]) + '(face' + str(elemAndFaceIDs1[m][1]) + ') fits elem ' + str(elemAndFaceIDs2[idx][0]) + '(face' + str(elemAndFaceIDs2[idx][1]) + ')')
            progWin.setValue(m)
            QApplication.processEvents()
    return 1
