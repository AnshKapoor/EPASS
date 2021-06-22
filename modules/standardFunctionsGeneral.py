#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
from PyQt5.QtWidgets import QApplication
import numpy as np
import vtk
from standardWidgets import progressWindow, messageboxOK

# Read Nodes from cub5 and save them into hdf5 OR only read nodes directly from hdf5
def readNodes(myModel, hdf5File, cub5File=0):
    if cub5File: 
        progWin = progressWindow(2, 'Loading nodes ...')
        # Nodes 
        nodesInv = dict([[ID, n] for n, ID in enumerate(cub5File['Mesh/Nodes/Node IDs'][:])])
        #
        progWin.setValue(1)
        QApplication.processEvents()
        myModel.allUsedNodesIdx = [nodesInv[nodeId] for nodeId in np.unique(myModel.allUsedNodes)]
        #
        g = hdf5File.create_group('Nodes')
        comp_type = np.dtype([('Ids', 'i8'), ('xCoords', 'f8'), ('yCoords', 'f8'), ('zCoords', 'f8')])
        dataSet = g.create_dataset('mtxFemNodes', (len(myModel.allUsedNodesIdx),), comp_type)
        dataSet[:,'Ids'] = np.array(cub5File['Mesh/Nodes/Node IDs'][sorted(myModel.allUsedNodesIdx)], dtype=np.uint64)
        dataSet[:,'xCoords'] = cub5File['Mesh/Nodes/X Coords'][sorted(myModel.allUsedNodesIdx)]
        dataSet[:,'yCoords'] = cub5File['Mesh/Nodes/Y Coords'][sorted(myModel.allUsedNodesIdx)]
        dataSet[:,'zCoords'] = cub5File['Mesh/Nodes/Z Coords'][sorted(myModel.allUsedNodesIdx)]
        myModel.nodesInv = dict([[ID, n] for n, ID in enumerate(dataSet[:,'Ids'])])
        progWin.setValue(2)
        QApplication.processEvents()
        if len(myModel.nodesInv)<len(nodesInv):
            messageboxOK('Ignored nodes', str(len(nodesInv)-len(myModel.nodesInv)) + ' nodes have been ignored as no elements use these nodes.')
        nodesInv = 0
        # Nodesets 
        g = hdf5File.create_group('Nodesets')
        if 'Nodesets' in cub5File['Simulation Model'].keys(): # If nodesets exist in cub5 file by coreform, then read them
            for nodeset in cub5File['Simulation Model/Nodesets'].keys():
                nodesetID = cub5File['Simulation Model/Nodesets/' + nodeset].attrs['nodeset_id'][()][0]
                g.create_dataset('vecNodeset' + str(nodesetID), data=cub5File['Simulation Model/Nodesets/' + nodeset + '/member ids'][()])
                g['vecNodeset' + str(nodesetID)].attrs['Id'] = np.uint64(nodesetID)
        myModel.nodes = hdf5File['Nodes/mtxFemNodes']
    else:
        myModel.nodes = hdf5File['Nodes/mtxFemNodes']
        myModel.nodesInv = dict([[ID, n] for n, ID in enumerate(myModel.nodes[:,'Ids'])])
    for nodeset in hdf5File['Nodesets'].keys():
        myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])

# Read Elements from cub5 and save them into hdf5 OR only read elements directly from hdf5
def readElements(myModel, hdf5File, cub5File=0):
    if cub5File: 
        myModel.allUsedNodes = []
        g = hdf5File.create_group('Elements')
        # Prepare dictionary for faster elem id search
        maxElemID = 0
        for coreformKey in cub5File['Mesh/Elements'].keys():
            myModel.elemsInvTags.append(coreformKey)
            elemIDs = cub5File['Mesh/Elements/' + coreformKey + '/Element IDs'][:]
            if elemIDs.max()>maxElemID:
                maxElemID = elemIDs.max()
            myModel.elemsInv.append(dict([[ID, n] for n, ID in enumerate(elemIDs)]))
        # Sort blocks according to ID
        groupIDs = []
        allBlocks = []
        for block in cub5File['Simulation Model/Blocks'].keys():
            groupIDs.append(cub5File['Simulation Model/Blocks/' + block].attrs['block_id'][()][0])
            allBlocks.append(block)
        idx = np.argsort(np.array(groupIDs))
        allBlocks = [allBlocks[n] for n in idx]
        # Load blocks in correct ordering
        progWin = progressWindow(len(allBlocks)-1, 'Loading blocks ...')
        for p, block in enumerate(allBlocks):
            groupID = cub5File['Simulation Model/Blocks/' + block].attrs['block_id'][()][0]
            elemType = cub5File['Simulation Model/Blocks/' + block].attrs['element_type'][()]
            coreformKey, elemType, M = identifyElemType(elemType)
            N = cub5File['Simulation Model/Blocks/' + block].attrs['num_members'][()][0]
            if coreformKey != 'notSupported':
                dataSet = createInitialBlockDataSet(g, elemType, groupID, N, M)
                memberIDs = (cub5File['Simulation Model/Blocks/' + block + '/member ids'][:].T).tolist()[0]
                if coreformKey == 'NODES': 
                    dataSet[:,0] = np.array([x for x in range(maxElemID+1,maxElemID+1+len(memberIDs))]) # Generate new elem ids as coreform does not deliver those
                    dataSet[:,1] = np.array(memberIDs)
                    maxElemID = maxElemID+len(memberIDs)
                else:
                    elemsInv = myModel.elemsInv[myModel.elemsInvTags.index(coreformKey)]
                    idx = [elemsInv[elemID] for elemID in memberIDs]
                    dataSet[:,0] = np.array([cub5File['Mesh/Elements/' + coreformKey + '/Global IDs'][currentID] for currentID in idx])
                    dataSet[:,1:] = np.array([cub5File['Mesh/Elements/' + coreformKey + '/Connectivity'][currentID,:] for currentID in idx])
                    if len(myModel.allUsedNodes) != 0:
                        myModel.allUsedNodes = np.append(myModel.allUsedNodes, dataSet[:,1:].flatten())
                    else:
                        myModel.allUsedNodes = dataSet[:,1:].flatten()
                myModel.elems.append(dataSet)
            progWin.setValue(p)
            QApplication.processEvents()
        #newNodes = myModel.nodes
        # Element-/Sidesets 
        g = hdf5File.create_group('Elementsets')
        #if 'Sidesets' in cub5File['Simulation Model'].keys(): # If sidesets exist in cub5 file by coreform, then read them as element sets
        #    for elemset in cub5File['Simulation Model/Sidesets'].keys():
        #        elemsetID = cub5File['Simulation Model/Sidesets/' + elemset].attrs['sideset_id'][()][0]
        #        ###
        #        # This line is required to identify global ids, implementation not finished.
        #        idx = [np.where(elemIDs[:] == elemID)[0][0] for elemID in cub5File['Simulation Model/Sidesets/' + elemset + '/member ids'][:].T]
        #        ###
        #        # Currently here are local (face / hex) number saved, which is not working if elemsets are used!
        #        g.create_dataset('vecElemset' + str(elemsetID), data=cub5File['Simulation Model/Sidesets/' + elemset + '/member ids'][()])
        #        g['vecElemset' + str(elemsetID)].attrs['Id'] = np.uint64(elemsetID)
    else:
        for block in hdf5File['Elements'].keys():
            myModel.elems.append(hdf5File['Elements/' + block])
    for elemset in hdf5File['Elementsets'].keys():
        myModel.elementSets.append(hdf5File['Elementsets/' + elemset])


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

def getFieldIndices(nodes, nodesInv, elems): 
    supportedFields = getSupportedFields()
    dofPattern = np.zeros((len(nodes), len(supportedFields)), dtype=np.bool_)
    for block in elems: 
      dofInElement = getElementDof(block.attrs['ElementType'])
      dofLine = [True if dof in dofInElement else False for dof in supportedFields]
      for element in block:
        nodeIdx = [nodesInv[nodeId] for nodeId in element[1:]]
        dofPattern[sorted(nodeIdx), :] = (dofLine + dofPattern[sorted(nodeIdx), :])
    dofPerNode = np.sum(dofPattern, axis=1)
    startIdxPerNode = np.cumsum(dofPerNode)-dofPerNode[0]
    nodesPerDof = np.sum(dofPattern, axis=0)
    availableFields = []
    fieldIndices = []
    for n, field in enumerate(supportedFields): 
      if nodesPerDof[n]>0: 
        availableFields.append(field)
        fieldIndices.append(startIdxPerNode[dofPattern[:,n]] + np.sum(dofPattern[:,0:n], axis=1))
    return availableFields, fieldIndices

def getSupportedFields():
    return ['displacement x', 'displacement y', 'displacement z', 'rotation x', 'rotation y', 'rotation z', 'sound pressure']

def getElementDof(elemType): 
    if elemType in ['DSG4','DSG8','DSG9']:
        return ['displacement z', 'rotation x', 'rotation y']
    elif elemType in ['Disc4','Disc9']:
        return ['displacement x', 'displacement y']
    elif elemType in ['PlShell4','PlShell9','PlShell9pre']: 
        return ['displacement x', 'displacement y', 'displacement z', 'rotation x', 'rotation y', 'rotation z']
    elif elemType in ['Fluid8','Fluid27']:
        return ['sound pressure']
    elif elemType in ['Brick8','Brick20','Brick27']:
        return ['displacement x', 'displacement y', 'displacement z']
    else:
        return []

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
    if elemType[0] == 20: #Quadrilateral with 4 nodes
        return 'QUAD_4', 'PlShell4', 5;
    elif elemType[0] == 22: # Quadrilateral with 9 nodes
        return 'QUAD_9', 'PlShell9', 10;
    elif elemType[0] == 40: # Hexahedron with 8 nodes
        return 'HEX_NODE_8', 'Fluid8', 9;
    elif elemType[0] == 43: # Hexahedron with 27 nodes
        return 'HEX_NODE_27', 'Fluid27', 28; 
    elif elemType[0] == 10: # 2-node Spring
        return 'EDGE_2', 'Spring', 3; 
    elif elemType[0] == 0: # point elemenets (for bc springs or point mass)
        return 'NODES', 'Pointmass', 2; 
    else:
        return 'notSupported', [], 0;

def identifyAlternativeElemTypes(elemType):
    if elemType in ['PlShell4','DSG4']:
        return ['PlShell4','DSG4'];
    elif elemType in ['PlShell9','PlShell9pre','DSG9','Disc9','Fluid2d9']: 
        return ['PlShell9pre','PlShell9','DSG9','Disc9','Fluid2d9'];
    elif elemType in ['Fluid8','Brick8']:
        return ['Fluid8','Brick8'];
    elif elemType in ['Fluid27','Brick27']:
        return ['Fluid27','Brick27'];
    elif elemType in ['Spring']:
        return ['Spring'];
    elif elemType in ['Pointmass','SpringBCx','SpringBCy','SpringBCz','SpringBCrx','SpringBCry','SpringBCrz']:
        return ['Pointmass','SpringBCx','SpringBCy','SpringBCz','SpringBCrx','SpringBCry','SpringBCrz']
    else:
        return [];

def identifyOrientationTypes(elemType):
    if elemType in ['Brick27']: 
        return ['global','user-def'];
    else:
        return ['global'];
    
def getPossibleInterfacePartner(elemType):
    if elemType in ['PlShell9', 'PlShell9pre','DSG9']:
        return ['Fluid27']
    elif elemType in ['Fluid27']:
        return ['PlShell9', 'PlShell9pre','DSG9']
    elif elemType in ['Fluid8']:
        return ['PlShell4', 'DSG4']
    elif elemType in ['PlShell4', 'DSG4']:
        return ['Fluid8']
    else:
        return []
    
def isPlateType(elemType):
    if elemType in ['PlShell9', 'PlShell9pre','DSG9','PlShell4','DSG4']:
        return 1
    else:
        return 0

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
    elif elemType in ['PlShell4','DSG4']:
        return np.array([[0,1,2,3]]) # Face 0
    elif elemType in ['Fluid8','Brick8','Disc4','Fluid2d4']:
        return np.array([[0,1,5,4],
                         [2,3,7,6],
                         [0,3,2,1],
                         [1,2,6,5],
                         [4,5,6,7],
                         [0,4,7,3]]) # Face 0,1,2,3,4,5
    else:
        return []

def getVTKElem(elpasoElemType):
    if elpasoElemType in ['DSG4','DSG9','PlShell4','PlShell9','PlShell9pre','Disc9','Fluid2d9']:
        return vtk.vtkQuad(), 9, 4
    elif elpasoElemType in ['Fluid8','Fluid27','Brick8','Brick20','Brick27']:
        return vtk.vtkHexahedron(), 12, 8
    elif elpasoElemType in ['Spring']:
        return vtk.vtkLine(), 3, 2
    elif elpasoElemType in ['Pointmass','SpringBCx','SpringBCy','SpringBCz','SpringBCrx','SpringBCry','SpringBCrz']:
        return vtk.vtkVertex(), 1, 1
    else:
        return 0, 0, 0
   
def searchInterfaceElems(nodes, nodesInv, elems, blockCombinations, tolerance=1e-3):
    foundInterFaceElementsBlocks = []
    # Collect all hexa (first) blocks for speed up (just collecting coordinates once)
    hexaBlocks = list(set([blockCombi[0] for blockCombi in blockCombinations]))
    for hexaBlock in hexaBlocks:
        # change number of faces
        nodeIdxOfFaces1 = getNodeIdxOfFaces(elems[hexaBlock].attrs['ElementType'])
        # Get sizes
        noOfElems1 = len(elems[hexaBlock])
        noOfFaces1 = nodeIdxOfFaces1.shape[0]
        noOfTotalFaces1 = noOfElems1 * noOfFaces1
        # Init arrays containing all coordinates
        elemAndFaceIDs1 = []
        xCoords1 = np.zeros((noOfTotalFaces1,4))
        yCoords1 = np.zeros((noOfTotalFaces1,4))
        zCoords1 = np.zeros((noOfTotalFaces1,4))
        # Loops to collect coordinates in block 1
        progWin = progressWindow(len(elems[hexaBlock])-1, 'Collecting coordinates of block' + str(elems[hexaBlock].attrs['Id']))
        for m, elem1 in enumerate(elems[hexaBlock]):
            for faceNo1 in range(noOfFaces1): 
                nodeIdx1 = [nodesInv[nodeID] for nodeID in elem1[nodeIdxOfFaces1[faceNo1,:4]+1]] # indices of nodes belonging to the face
                xCoords1[m*noOfFaces1 + faceNo1,:] = np.sort(nodes[sorted(nodeIdx1)]['xCoords']) # Sorting necessary
                yCoords1[m*noOfFaces1 + faceNo1,:] = np.sort(nodes[sorted(nodeIdx1)]['yCoords'])
                zCoords1[m*noOfFaces1 + faceNo1,:] = np.sort(nodes[sorted(nodeIdx1)]['zCoords'])
                elemAndFaceIDs1.append([m, faceNo1])
            progWin.setValue(m)
            QApplication.processEvents()
        # Now loop over fitting second blocks and re-use coords of (potentially larger) hexa block
        for blockCombi in blockCombinations:
            if blockCombi[0] == hexaBlock:
                foundInterFaceElements = []
                # change number of faces
                nodeIdxOfFaces2 = getNodeIdxOfFaces(elems[blockCombi[1]].attrs['ElementType'])
                # Get sizes
                noOfElems2 = len(elems[blockCombi[1]])
                noOfFaces2 = nodeIdxOfFaces2.shape[0]
                noOfTotalFaces2 = noOfElems2 * noOfFaces2
                # Init arrays containing all coordinates
                elemAndFaceIDs2 = []
                xCoords2 = np.zeros((noOfTotalFaces2,4))
                yCoords2 = np.zeros((noOfTotalFaces2,4))
                zCoords2 = np.zeros((noOfTotalFaces2,4))
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
                    xIdx = ((abs(xCoords2[:,0]-xCoords1[m,0])<tolerance) & (abs(xCoords2[:,1]-xCoords1[m,1])<tolerance) & (abs(xCoords2[:,2]-xCoords1[m,2])<tolerance) & (abs(xCoords2[:,3]-xCoords1[m,3])<tolerance))
                    yIdx = ((abs(yCoords2[:,0]-yCoords1[m,0])<tolerance) & (abs(yCoords2[:,1]-yCoords1[m,1])<tolerance) & (abs(yCoords2[:,2]-yCoords1[m,2])<tolerance) & (abs(yCoords2[:,3]-yCoords1[m,3])<tolerance))
                    zIdx = ((abs(zCoords2[:,0]-zCoords1[m,0])<tolerance) & (abs(zCoords2[:,1]-zCoords1[m,1])<tolerance) & (abs(zCoords2[:,2]-zCoords1[m,2])<tolerance) & (abs(zCoords2[:,3]-zCoords1[m,3])<tolerance))
                    if True in (xIdx & yIdx & zIdx):
                        # Compute normal of elem 1 using original order 
                        elem1 = elems[blockCombi[0]][elemAndFaceIDs1[m][0]]
                        nodeIdx1 = [nodesInv[nodeID] for nodeID in elem1[nodeIdxOfFaces1[elemAndFaceIDs1[m][1],:4]+1]]
                        elem1x = [nodes[idx]['xCoords'] for idx in nodeIdx1]
                        elem1y = [nodes[idx]['yCoords'] for idx in nodeIdx1]
                        elem1z = [nodes[idx]['zCoords'] for idx in nodeIdx1]
                        a1 = [elem1x[1] - elem1x[0], elem1y[1] - elem1y[0], elem1z[1] - elem1z[0]]
                        b1 = [elem1x[3] - elem1x[0], elem1y[3] - elem1y[0], elem1z[3] - elem1z[0]]
                        normal1 = np.cross(a1,b1)
                        normal1 = normal1 / np.linalg.norm(normal1)
                        # Compute normal of elem 2
                        idx = (xIdx & yIdx & zIdx).nonzero()[0][0]
                        elem2 = elems[blockCombi[1]][elemAndFaceIDs2[idx][0]]
                        nodeIdx2 = [nodesInv[nodeID] for nodeID in elem2[nodeIdxOfFaces2[elemAndFaceIDs2[idx][1],:4]+1]]
                        elem2x = [nodes[idx]['xCoords'] for idx in nodeIdx2]
                        elem2y = [nodes[idx]['yCoords'] for idx in nodeIdx2]
                        elem2z = [nodes[idx]['zCoords'] for idx in nodeIdx2]
                        a2 = [elem2x[1] - elem2x[0], elem2y[1] - elem2y[0], elem2z[1] - elem2z[0]]
                        b2 = [elem2x[3] - elem2x[0], elem2y[3] - elem2y[0], elem2z[3] - elem2z[0]]
                        normal2 = np.cross(a2,b2)
                        normal2 = normal2 / np.linalg.norm(normal2)
                        # Identify orientation
                        cosineOfAngle = np.dot(normal1, normal2)
                        if cosineOfAngle > 0: # Normal vector show in equal direction
                            ori = -1
                        else:
                            ori = 1
                        foundInterFaceElements.append(interfaceElement())
                        foundInterFaceElements[-1].ori = ori
                        matchingNodes=[-1,-1] # First and second matching node
                        # The order of nodes must be considered (matching nodes must be given at the same index!); 8 cases of face rotations are possible, the midside nodes are assumed to be coincident.
                        for n in range(4):
                            if (abs(elem1x[0] - elem2x[n])<tolerance) and (abs(elem1y[0] - elem2y[n])<tolerance) and (abs(elem1z[0] - elem2z[n])<tolerance): 
                                matchingNodes[0] = n
                            if (abs(elem1x[1] - elem2x[n])<tolerance) and (abs(elem1y[1] - elem2y[n])<tolerance) and (abs(elem1z[1] - elem2z[n])<tolerance): 
                                matchingNodes[1] = n
                        if matchingNodes==[0,1]: 
                            matchingNodeIdx = [0,1,2,3,4,5,6,7,8]
                        elif matchingNodes==[0,3]: 
                            matchingNodeIdx = [0,3,2,1,7,6,5,4,8]
                        elif matchingNodes==[1,2]: 
                            matchingNodeIdx = [1,2,3,0,5,6,7,4,8]
                        elif matchingNodes==[1,0]: 
                            matchingNodeIdx = [1,0,3,2,4,7,6,5,8]
                        elif matchingNodes==[2,3]: 
                            matchingNodeIdx = [2,3,0,1,6,7,4,5,8]
                        elif matchingNodes==[2,1]: 
                            matchingNodeIdx = [2,1,0,3,5,4,7,6,8]
                        elif matchingNodes==[3,0]: 
                            matchingNodeIdx = [3,0,1,2,7,4,5,6,8]
                        elif matchingNodes==[3,2]: 
                            matchingNodeIdx = [3,2,1,0,6,5,4,7,8]
                        else:
                            pass
                        #
                        if not -1 in matchingNodeIdx:
                            foundInterFaceElements[-1].fluidNodes = [np.uint64(nodeID) for nodeID in elem1[nodeIdxOfFaces1[elemAndFaceIDs1[m][1],:]+1]]
                            foundInterFaceElements[-1].structuralNodes = [np.uint64(nodeID) for nodeID in elem2[nodeIdxOfFaces2[elemAndFaceIDs2[idx][1],matchingNodeIdx[:nodeIdxOfFaces1.shape[1]]]+1]]
                            foundInterFaceElements[-1].structElemId = np.uint64(elem2[0])
                            foundInterFaceElements[-1].fluidBlockIdx = blockCombi[0]
                            foundInterFaceElements[-1].structBlockIdx = blockCombi[1]
                        #print('Elem ' + str(elems[blockCombi[0]][elemAndFaceIDs1[m][0]][0]) + '(face' + str(elemAndFaceIDs1[m][1]) + ') fits elem ' + str(elems[blockCombi[1]][elemAndFaceIDs2[idx][0]][0]) + '(face' + str(elemAndFaceIDs2[idx][1]) + ')')
                    progWin.setValue(m)
                    QApplication.processEvents()
                if foundInterFaceElements != []:
                    foundInterFaceElementsBlocks.append(foundInterFaceElements)
    return foundInterFaceElementsBlocks

class interfaceElement: # Define an interface element
    def __init__(self):
        self.Id = np.uint64(0)
        self.type = 'undefined'
        self.ori = np.int64(0)
        self.structBlockIdx = np.uint64(0)
        self.fluidBlockIdx = np.uint64(0)
        self.structElemId = np.uint64(0)
        self.structuralNodes = []
        self.fluidNodes = []
        self.fluidMaterialId = np.uint64(0)
        self.structuralMaterialId = np.uint64(0)
        