#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
from PyQt5.QtWidgets import QApplication
import numpy as np
import scipy.spatial.distance
import vtk
from standardWidgets import progressWindow, messageboxOK
from itertools import compress

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

def getFieldIndices(nodes, orderIdx, nodesInv, elems): 
    supportedFields = getSupportedFields()
    dofPattern = np.zeros((len(nodes), len(supportedFields)), dtype=np.bool_)
    for block in elems: 
      dofInElement = getElementDof(block.attrs['ElementType'])
      dofLine = [True if dof in dofInElement else False for dof in supportedFields]
      for element in block:
        nodeIdx = [orderIdx[nodeId] for nodeId in element[1:]]
        dofPattern[sorted(nodeIdx), :] = (dofLine + dofPattern[sorted(nodeIdx), :])
    dofPerNode = np.sum(dofPattern, axis=1)
    startIdxPerNode = np.cumsum(dofPerNode)-dofPerNode
    nodesPerDof = np.sum(dofPattern, axis=0)
    availableFields = []
    fieldIndices = []
    nodeIndices = []
    for n, field in enumerate(supportedFields): 
      if nodesPerDof[n]>0: 
        availableFields.append(field)
        fieldIndices.append(startIdxPerNode[dofPattern[:,n]] + np.sum(dofPattern[:,0:n], axis=1)[dofPattern[:,n]])
        nodeIndices.append(np.nonzero(dofPattern[:,n])[0])
    return availableFields, fieldIndices, nodeIndices, startIdxPerNode

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
    elif elemType in ['BeamBernoulli', 'BeamTimoshenko']:
        return ['displacement x', 'displacement y','rotation z']
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
    elif elemType[0] == 4: # beam elements
        return 'EDGE_2', 'BeamBernoulli', 3;
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
    elif elemType in ['Beam','BeamBernoulli','BeamBernoulli10','BeamBernoulli12','BeamTimoshenko', 'BeamTimoshenko10', 'BeamTimoshenko12']:
        return ['Beam','BeamBernoulli','BeamBernoulli10','BeamBernoulli12','BeamTimoshenko', 'BeamTimoshenko10', 'BeamTimoshenko12']
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
    
def isFluid3DType(elemType):
    if elemType in ['Fluid27','Fluid20','Fluid8']:
        return 1
    else:
        return 0
    
def isStructure3DType(elemType):
    if elemType in ['Brick27','Brick20','Brick8']:
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
    elif elpasoElemType in ['Spring','Beam','BeamBernoulli','BeamBernoulli10','BeamBernoulli12','BeamTimoshenko', 'BeamTimoshenko10', 'BeamTimoshenko12']:
        return vtk.vtkLine(), 3, 2
    elif elpasoElemType in ['Pointmass','SpringBCx','SpringBCy','SpringBCz','SpringBCrx','SpringBCry','SpringBCrz']:
        return vtk.vtkVertex(), 1, 1
    else:
        return 0, 0, 0

# Function to calculated angle in polar coordinates considering the quadrants (input: x,y of same length; outputs contains element-wise calculated angles)
def computePolarAngle(y, x):
    if len(x) != len(y): 
        print('Error in computePolarAngle: x and y arrays are not of same length.')
        return []
    angles = np.zeros(len(x))
    for idx, x1 in enumerate(x):
        y1 = y[idx]
        if abs(x1)<1e-12: 
            if y1>0: 
                angles[idx] = np.pi/2.
            elif y1<0: 
                angles[idx] = 1.5*np.pi
            else:
                angles[idx] =  0.
        elif x1>0. and y1>=0:
            angles[idx] = np.arctan(y1/x1)
        elif x1>0. and y1<0:
            angles[idx] = np.arctan(y1/x1) + 2*np.pi
        else: # x1<0.
            angles[idx] = np.arctan(y1/x1) + np.pi
    return angles

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

def searchNCInterfaceElemsSurface(nodes, nodesInv, elems, blockCombinations, interNodesMaxId, mode='plane', tolerance=1e-6):
    foundNCInterFaceElementsBlocks = []
    # Collect all hexa (first) blocks for speed up (just collecting coordinates once)
    hexaBlocks = list(set([blockCombi[0] for blockCombi in blockCombinations]))
    for hexaBlock in hexaBlocks:
        # change number of faces
        nodeIdxOfFaces1 = getNodeIdxOfFaces(elems[hexaBlock].attrs['ElementType'])
        # Get sizes
        noOfElems1 = len(elems[hexaBlock])
        noOfFaces1 = nodeIdxOfFaces1.shape[0]
        noOfFaceNodes = nodeIdxOfFaces1.shape[1]
        noOfTotalFaces1 = noOfElems1 * noOfFaces1
        # Init arrays containing all coordinates
        elemAndFaceIDs1 = []
        # Loops to collect coordinates in block 1
        progWin = progressWindow(len(elems[hexaBlock])-1, 'Collecting coordinates of block ' + str(elems[hexaBlock].attrs['Id']))
        for m, elem1 in enumerate(elems[hexaBlock]):
            for faceNo1 in range(noOfFaces1): 
                elemAndFaceIDs1.append([m, faceNo1])
            progWin.setValue(m)
            QApplication.processEvents()
        # Now loop over fitting second blocks and re-use coords of (potentially larger) hexa block
        interNodeCounter = 0
        for blockCombi in blockCombinations:
            if blockCombi[0] == hexaBlock:
                foundNCInterFaceElements = []
                generatedInterNodesIds = []
                generatedInterNodesCoords = []
                # change number of faces
                nodeIdxOfFaces2 = getNodeIdxOfFaces(elems[blockCombi[1]].attrs['ElementType'])
                # Get sizes
                noOfElems2 = len(elems[blockCombi[1]])
                noOfFaces2 = nodeIdxOfFaces2.shape[0]
                noOfTotalFaces2 = noOfElems2 * noOfFaces2
                # Init arrays containing all coordinates
                elemAndFaceIDs2 = []
                # Loops to collect coordinates in block 2
                progWin = progressWindow(len(elems[blockCombi[1]])-1, 'Collecting coordinates of block ' + str(elems[blockCombi[1]].attrs['Id']))
                for m, elem2 in enumerate(elems[blockCombi[1]]): 
                    for faceNo2 in range(noOfFaces2):
                        elemAndFaceIDs2.append([m, faceNo2])
                    progWin.setValue(m)
                    QApplication.processEvents()
                ### searchNCInterfaceElemsSurface is split here: Modes planes and cylinder are supported ### 
                if mode == 'plane':
                    # Compute shell block plane based on first face
                    elem2 = elems[blockCombi[1]][elemAndFaceIDs2[0][0]]
                    nodeIdx2 = [nodesInv[nodeID] for nodeID in elem2[nodeIdxOfFaces2[elemAndFaceIDs2[0][1],:4]+1]]
                    elem2x = [nodes[idx]['xCoords'] for idx in nodeIdx2]
                    elem2y = [nodes[idx]['yCoords'] for idx in nodeIdx2]
                    elem2z = [nodes[idx]['zCoords'] for idx in nodeIdx2]
                    a2 = [elem2x[1] - elem2x[0], elem2y[1] - elem2y[0], elem2z[1] - elem2z[0]]
                    b2 = [elem2x[3] - elem2x[0], elem2y[3] - elem2y[0], elem2z[3] - elem2z[0]]
                    planeNormal = np.cross(a2,b2)
                    planeNormal = planeNormal / np.linalg.norm(planeNormal)
                    planeOrigin = np.array([elem2x[0], elem2y[0], elem2z[0]])
                    planeOriginDistance = np.dot(planeNormal, planeOrigin)
                    # Check if all shell block faces are within this plane
                    for faceIdx in range(noOfTotalFaces2):
                        elem2 = elems[blockCombi[1]][elemAndFaceIDs2[faceIdx][0]]
                        nodeIdx2 = [nodesInv[nodeID] for nodeID in elem2[nodeIdxOfFaces2[elemAndFaceIDs2[faceIdx][1],:4]+1]]
                        elem2x = [nodes[idx]['xCoords'] for idx in nodeIdx2]
                        elem2y = [nodes[idx]['yCoords'] for idx in nodeIdx2]
                        elem2z = [nodes[idx]['zCoords'] for idx in nodeIdx2]
                        a2 = [elem2x[1] - elem2x[0], elem2y[1] - elem2y[0], elem2z[1] - elem2z[0]]
                        b2 = [elem2x[3] - elem2x[0], elem2y[3] - elem2y[0], elem2z[3] - elem2z[0]]
                        normal2 = np.cross(a2,b2)
                        normal2 = normal2 / np.linalg.norm(normal2)
                        if not abs(abs(np.dot(planeNormal, normal2))-1.)<1e-9: 
                            messageboxOK('Error', 'The nodes of block ' + str(elems[blockCombi[1]].attrs['Id']) + ' are not within a plane!.')
                            return []
                    # Find faces of hexa block in the shell plane
                    relevantElemAndFaceIDs1 = []
                    relevantElemAndFaceIDs2  = elemAndFaceIDs2
                    progWin = progressWindow(noOfTotalFaces1-1, 'Finding faces of hexa block in the plane')
                    for faceIdx in range(noOfTotalFaces1):
                        elem1 = elems[blockCombi[0]][elemAndFaceIDs1[faceIdx][0]]
                        nodeIdx1 = [nodesInv[nodeID] for nodeID in elem1[nodeIdxOfFaces1[elemAndFaceIDs1[faceIdx][1],:4]+1]]
                        elem1x = [nodes[idx]['xCoords'] for idx in nodeIdx1]
                        elem1y = [nodes[idx]['yCoords'] for idx in nodeIdx1]
                        elem1z = [nodes[idx]['zCoords'] for idx in nodeIdx1]
                        a2 = [elem1x[1] - elem1x[0], elem1y[1] - elem1y[0], elem1z[1] - elem1z[0]]
                        b2 = [elem1x[3] - elem1x[0], elem1y[3] - elem1y[0], elem1z[3] - elem1z[0]]
                        normal1 = np.cross(a2,b2)
                        normal1 = normal1 / np.linalg.norm(normal1)
                        # Check if normals are equal
                        if not abs(abs(np.dot(planeNormal, normal1))-1.)<1e-9: 
                            pass
                        else:
                            # Check distance to plane
                            if abs(np.dot(planeNormal, [elem1x[0], elem1y[0], elem1z[0]]) - planeOriginDistance)<1e-9:
                                relevantElemAndFaceIDs1.append(elemAndFaceIDs1[faceIdx])
                                #print(elem1[0])
                        progWin.setValue(faceIdx)
                        QApplication.processEvents()
                    # Identify corners of rectangle (nodes of relevant faces, which are included in one face only)
                    noOfTotalRelevantFaces1 = len(relevantElemAndFaceIDs1)
                    noOfTotalRelevantFaces2 = len(relevantElemAndFaceIDs2)
                    relevantNodes1 = []
                    relevantNodes2 = []
                    for faceIdx in range(noOfTotalRelevantFaces1):
                        elem1 = elems[blockCombi[0]][relevantElemAndFaceIDs1[faceIdx][0]]
                        [relevantNodes1.append(nodeID) for nodeID in elem1[nodeIdxOfFaces1[relevantElemAndFaceIDs1[faceIdx][1],:4]+1]]
                    for faceIdx in range(noOfTotalRelevantFaces2):
                        elem2 = elems[blockCombi[1]][relevantElemAndFaceIDs2[faceIdx][0]]
                        [relevantNodes2.append(nodeID) for nodeID in elem2[nodeIdxOfFaces2[relevantElemAndFaceIDs2[faceIdx][1],:4]+1]]
                    edgeNodesIdx1 = [nodesInv[relevantNodes1[idx]] for idx, count in enumerate([relevantNodes1.count(nodeID) for nodeID in relevantNodes1]) if count == 1]
                    #edgeNodesIdx2 = [nodesInv[relevantNodes2[idx]] for idx, count in enumerate([relevantNodes2.count(nodeID) for nodeID in relevantNodes2]) if count == 1]
                    relevantNodesIdx1 = [nodesInv[nodeID] for nodeID in relevantNodes1]
                    relevantNodesIdx2 = [nodesInv[nodeID] for nodeID in relevantNodes2]
                    # Compute local coordinate system with rectangular limits of interface
                    edgeNodes1Coords = np.array([[nodes[idx]['xCoords'],nodes[idx]['yCoords'],nodes[idx]['zCoords']] for idx in edgeNodesIdx1])
                    distMatrix1 = scipy.spatial.distance.cdist(edgeNodes1Coords,edgeNodes1Coords)
                    originRectangle1 = edgeNodes1Coords[0,:] # Origin of the rectangular coordinate system
                    coordSysNodesIdx1 = edgeNodesIdx1[1:]
                    coordSysNodesIdx1.pop(np.argmax(distMatrix1[1:,:])) # This list now contains the two nearest edge nodes, which span the rectangular shape correctly
                    coordSysNodesCoords = np.array([[nodes[idx]['xCoords'],nodes[idx]['yCoords'],nodes[idx]['zCoords']] for idx in coordSysNodesIdx1])
                    axis1Rectangle1 = coordSysNodesCoords[0,:] - originRectangle1
                    axis1Rectangle1 = axis1Rectangle1 / np.linalg.norm(axis1Rectangle1)
                    axis2Rectangle1 = coordSysNodesCoords[1,:] - originRectangle1
                    axis2Rectangle1 = axis2Rectangle1 / np.linalg.norm(axis2Rectangle1)
                    axis3Rectangle1 = np.cross(axis1Rectangle1,axis2Rectangle1)
                    axis3Rectangle1 = axis3Rectangle1 / np.linalg.norm(axis3Rectangle1) # The third axis / normal
                    T = np.array([axis1Rectangle1, axis2Rectangle1, axis3Rectangle1]) # Transition matrix (global to in-plane coordinate system)
                    Tinv = np.linalg.inv(T)
                    # Compute local coordinates of all relevant nodes
                    relevantNodes1Coords = np.array([T.dot([nodes[idx]['xCoords']-originRectangle1[0],nodes[idx]['yCoords']-originRectangle1[1],nodes[idx]['zCoords']-originRectangle1[2]]) for idx in relevantNodesIdx1])
                    relevantNodes2Coords = np.array([T.dot([nodes[idx]['xCoords']-originRectangle1[0],nodes[idx]['yCoords']-originRectangle1[1],nodes[idx]['zCoords']-originRectangle1[2]]) for idx in relevantNodesIdx2])
                    limitsFaces1 = np.zeros((len(relevantElemAndFaceIDs1), 4)) # 2 min; 2 max (1 min /1 max per local axis)
                    limitsFaces2 = np.zeros((len(relevantElemAndFaceIDs2), 4)) 
                    midFaces1 = np.zeros((len(relevantElemAndFaceIDs1), 2)) 
                    midFaces2 = np.zeros((len(relevantElemAndFaceIDs2), 2)) 
                    elems1 = np.zeros((len(relevantElemAndFaceIDs1), noOfFaceNodes+1), dtype=np.int64) # One ID, 4 or 9 node IDs
                    elems2 = np.zeros((len(relevantElemAndFaceIDs2), noOfFaceNodes+1), dtype=np.int64)
                    for idx1, ElemFaceCombi1 in enumerate(relevantElemAndFaceIDs1):
                        elems1[idx1,0] = elems[blockCombi[0]][ElemFaceCombi1[0],0]
                        elems1[idx1,1:noOfFaceNodes+1] = [elems[blockCombi[0]][ElemFaceCombi1[0],n+1] for n in nodeIdxOfFaces1[ElemFaceCombi1[1],:noOfFaceNodes]]
                        myCoords1 = relevantNodes1Coords[idx1*4:(idx1*4+4),:2] # Reuse coords and exclude z as its not important in plane
                        limitsFaces1[idx1, :2] = np.min(myCoords1, axis=0)
                        limitsFaces1[idx1, 2:] = np.max(myCoords1, axis=0)
                        midFaces1[idx1, :] = 0.5*(limitsFaces1[idx1, :2] + limitsFaces1[idx1, 2:])
                    for idx2, ElemFaceCombi2 in enumerate(relevantElemAndFaceIDs2):
                        elems2[idx2,0] = elems[blockCombi[1]][ElemFaceCombi2[0],0]
                        elems2[idx2,1:noOfFaceNodes+1] = [elems[blockCombi[1]][ElemFaceCombi2[0],n+1] for n in nodeIdxOfFaces2[ElemFaceCombi2[1],:noOfFaceNodes]]
                        myCoords2 = relevantNodes2Coords[idx2*4:(idx2*4+4),:2] # Reuse coords and exclude z as its not important in plane
                        limitsFaces2[idx2, :2] = np.min(myCoords2, axis=0)
                        limitsFaces2[idx2, 2:] = np.max(myCoords2, axis=0)
                        midFaces2[idx2, :] = 0.5*(limitsFaces2[idx2, :2] + limitsFaces2[idx2, 2:])
                elif mode == 'cylinder':
                    # Nothing to be computed (in comparison to plane) as cylinder is given by user
                    ### Fixed cylinder choice for testing instead of user input ###
                    cylinderAxis = np.array([0., 0., 1.]) # must be normalised!
                    cylinderOrigin= np.array([0., 0., 0.])
                    surfaceRadius = 1.3
                    ###############################################################
                    # Check if all shell block faces are within the cylinder surface
                    for faceIdx in range(noOfTotalFaces2):
                        elem2 = elems[blockCombi[1]][elemAndFaceIDs2[faceIdx][0]]
                        nodeIdx2 = [nodesInv[nodeID] for nodeID in elem2[nodeIdxOfFaces2[elemAndFaceIDs2[faceIdx][1],:4]+1]]
                        elem2x = [nodes[idx]['xCoords'] for idx in nodeIdx2]
                        elem2y = [nodes[idx]['yCoords'] for idx in nodeIdx2]
                        elem2z = [nodes[idx]['zCoords'] for idx in nodeIdx2]
                        # Distance calculation to cylinderAxis and check if equal to user-given radius
                        if False in (np.abs((np.linalg.norm(np.cross(np.array([elem2x, elem2y, elem2z]).T - cylinderOrigin, cylinderAxis), axis=1)-surfaceRadius)) < tolerance):
                            messageboxOK('Error', 'The nodes of block ' + str(elems[blockCombi[1]].attrs['Id']) + ' are not within the given cylinder!.')
                            return []
                    # Find faces of hexa block in the cylinder surface
                    relevantElemAndFaceIDs1 = []
                    relevantElemAndFaceIDs2  = elemAndFaceIDs2
                    progWin = progressWindow(noOfTotalFaces1-1, 'Finding faces of hexa block within cylinder surface')
                    for faceIdx in range(noOfTotalFaces1):
                        elem1 = elems[blockCombi[0]][elemAndFaceIDs1[faceIdx][0]]
                        nodeIdx1 = [nodesInv[nodeID] for nodeID in elem1[nodeIdxOfFaces1[elemAndFaceIDs1[faceIdx][1],:4]+1]]
                        elem1x = [nodes[idx]['xCoords'] for idx in nodeIdx1]
                        elem1y = [nodes[idx]['yCoords'] for idx in nodeIdx1]
                        elem1z = [nodes[idx]['zCoords'] for idx in nodeIdx1]
                        # Distance calculation to cylinderAxis and check if equal to user-given radius
                        if False in (np.abs((np.linalg.norm(np.cross(np.array([elem1x, elem1y, elem1z]).T - cylinderOrigin, cylinderAxis), axis=1) - surfaceRadius)) < tolerance):
                            pass
                        else: 
                            relevantElemAndFaceIDs1.append(elemAndFaceIDs1[faceIdx])
                        progWin.setValue(faceIdx)
                        QApplication.processEvents()
                    # Extraction of coordinates
                    noOfTotalRelevantFaces1 = len(relevantElemAndFaceIDs1)
                    noOfTotalRelevantFaces2 = len(relevantElemAndFaceIDs2)
                    relevantNodes1 = []
                    relevantNodes2 = []
                    for faceIdx in range(noOfTotalRelevantFaces1):
                        elem1 = elems[blockCombi[0]][relevantElemAndFaceIDs1[faceIdx][0]]
                        [relevantNodes1.append(nodeID) for nodeID in elem1[nodeIdxOfFaces1[relevantElemAndFaceIDs1[faceIdx][1],:4]+1]]
                    for faceIdx in range(noOfTotalRelevantFaces2):
                        elem2 = elems[blockCombi[1]][relevantElemAndFaceIDs2[faceIdx][0]]
                        [relevantNodes2.append(nodeID) for nodeID in elem2[nodeIdxOfFaces2[relevantElemAndFaceIDs2[faceIdx][1],:4]+1]]
                    relevantNodesIdx1 = [nodesInv[nodeID] for nodeID in relevantNodes1]
                    relevantNodesIdx2 = [nodesInv[nodeID] for nodeID in relevantNodes2]
                    # Compute local coordinate system with z axis equal to cylinderAxis and arbitrary but orthogonal x/y axes
                    arbitraryNodeCoordOnCylinder = np.array([elem2x, elem2y, elem2z])[:,0]
                    axis3Cyl = cylinderAxis
                    axis1Cyl = np.cross(axis3Cyl, arbitraryNodeCoordOnCylinder-cylinderOrigin)
                    axis1Cyl = axis1Cyl / np.linalg.norm(axis1Cyl)
                    axis2Cyl = np.cross(axis3Cyl, axis1Cyl)
                    axis2Cyl = axis2Cyl / np.linalg.norm(axis2Cyl)
                    T = np.array([axis1Cyl, axis2Cyl, axis3Cyl]).T # Transition matrix (global to z axis conform coordinate system)
                    Tinv = np.linalg.inv(T)
                    # Compute local coordinates of all relevant nodes - for phi, a shifted version is considered for clear identification of interfaces
                    relevantNodes1CartesianCoords = np.array([T.dot([nodes[idx]['xCoords']-cylinderOrigin[0],nodes[idx]['yCoords']-cylinderOrigin[1],nodes[idx]['zCoords']-cylinderOrigin[2]]) for idx in relevantNodesIdx1])
                    relevantNodes2CartesianCoords = np.array([T.dot([nodes[idx]['xCoords']-cylinderOrigin[0],nodes[idx]['yCoords']-cylinderOrigin[1],nodes[idx]['zCoords']-cylinderOrigin[2]]) for idx in relevantNodesIdx2])
                    relevantNodes1CylinderPhi = computePolarAngle(relevantNodes1CartesianCoords[:,1] , relevantNodes1CartesianCoords[:,0])
                    relevantNodes1CylinderPhiShifted = np.copy(relevantNodes1CylinderPhi) + np.pi
                    relevantNodes1CylinderPhiShifted[relevantNodes1CylinderPhiShifted>2*np.pi] = relevantNodes1CylinderPhiShifted[relevantNodes1CylinderPhiShifted>2*np.pi]-2*np.pi
                    relevantNodes2CylinderPhi = computePolarAngle(relevantNodes2CartesianCoords[:,1] , relevantNodes2CartesianCoords[:,0])
                    relevantNodes2CylinderPhiShifted = np.copy(relevantNodes2CylinderPhi) + np.pi
                    relevantNodes2CylinderPhiShifted[relevantNodes2CylinderPhiShifted>2*np.pi] = relevantNodes2CylinderPhiShifted[relevantNodes2CylinderPhiShifted>2*np.pi]-2*np.pi
                    limitsFaces1 = np.zeros((len(relevantElemAndFaceIDs1), 4)) # 2 min; 2 max (1 min /1 max per local axis, which are z and phi here)
                    limitsFaces2 = np.zeros((len(relevantElemAndFaceIDs2), 4)) 
                    midFaces1 = np.zeros((len(relevantElemAndFaceIDs1), 2)) 
                    midFaces2 = np.zeros((len(relevantElemAndFaceIDs2), 2)) 
                    limitsFaces1Shifted = np.zeros((len(relevantElemAndFaceIDs1), 4)) # 2 min; 2 max (1 min /1 max per local axis, which are z and phi here)
                    limitsFaces2Shifted = np.zeros((len(relevantElemAndFaceIDs2), 4)) 
                    midFaces1Shifted = np.zeros((len(relevantElemAndFaceIDs1), 2)) 
                    midFaces2Shifted = np.zeros((len(relevantElemAndFaceIDs2), 2)) 
                    elems1 = np.zeros((len(relevantElemAndFaceIDs1), noOfFaceNodes+1), dtype=np.int64) # One ID, 4 or 9 node IDs
                    elems2 = np.zeros((len(relevantElemAndFaceIDs2), noOfFaceNodes+1), dtype=np.int64)
                    for idx1, ElemFaceCombi1 in enumerate(relevantElemAndFaceIDs1):
                        elems1[idx1,0] = elems[blockCombi[0]][ElemFaceCombi1[0],0]
                        elems1[idx1,1:noOfFaceNodes+1] = [elems[blockCombi[0]][ElemFaceCombi1[0],n+1] for n in nodeIdxOfFaces1[ElemFaceCombi1[1],:noOfFaceNodes]]
                        myCoords1 = np.array([relevantNodes1CartesianCoords[idx1*4:(idx1*4+4),2],relevantNodes1CylinderPhi[idx1*4:(idx1*4+4)]]).T # Reuse coords from above
                        myCoords1Shifted = np.array([relevantNodes1CartesianCoords[idx1*4:(idx1*4+4),2],relevantNodes1CylinderPhiShifted[idx1*4:(idx1*4+4)]]).T # Reuse coords from above
                        limitsFaces1[idx1, :2] = np.min(myCoords1, axis=0)
                        limitsFaces1Shifted[idx1, :2] = np.min(myCoords1Shifted, axis=0)
                        limitsFaces1[idx1, 2:] = np.max(myCoords1, axis=0)
                        limitsFaces1Shifted[idx1, 2:] = np.max(myCoords1Shifted, axis=0)
                        midFaces1[idx1, 0] = 0.5*(limitsFaces1[idx1, 0] + limitsFaces1[idx1, 2]) # z coord mean
                        midFaces1[idx1, 1] = np.angle(np.exp(1j*limitsFaces1[idx1, 1])+np.exp(1j*limitsFaces1[idx1, 3])) # phi coord mean
                        if midFaces1[idx1, 1] < 0.:
                            midFaces1[idx1, 1] = midFaces1[idx1, 1] + 2*np.pi # correction to 0 ... 2pi
                        midFaces1Shifted[idx1, 0] = midFaces1[idx1, 0]
                        midFaces1Shifted[idx1, 1] = np.angle(np.exp(1j*limitsFaces1Shifted[idx1, 1])+np.exp(1j*limitsFaces1Shifted[idx1, 3])) # phi coord mean shifted
                        if midFaces1Shifted[idx1, 1] < 0.:
                            midFaces1Shifted[idx1, 1] = midFaces1Shifted[idx1, 1] + 2*np.pi # correction to 0 ... 2pi
                    for idx2, ElemFaceCombi2 in enumerate(relevantElemAndFaceIDs2):
                        elems2[idx2,0] = elems[blockCombi[1]][ElemFaceCombi2[0],0]
                        elems2[idx2,1:noOfFaceNodes+1] = [elems[blockCombi[1]][ElemFaceCombi2[0],n+1] for n in nodeIdxOfFaces2[ElemFaceCombi2[1],:noOfFaceNodes]]
                        myCoords2 = np.array([relevantNodes2CartesianCoords[idx2*4:(idx2*4+4),2],relevantNodes2CylinderPhi[idx2*4:(idx2*4+4)]]).T # Reuse coords from above
                        myCoords2Shifted = np.array([relevantNodes2CartesianCoords[idx2*4:(idx2*4+4),2],relevantNodes2CylinderPhiShifted[idx2*4:(idx2*4+4)]]).T # Reuse coords from above
                        limitsFaces2[idx2, :2] = np.min(myCoords2, axis=0)
                        limitsFaces2Shifted[idx2, :2] = np.min(myCoords2Shifted, axis=0)
                        limitsFaces2[idx2, 2:] = np.max(myCoords2, axis=0)
                        limitsFaces2Shifted[idx2, 2:] = np.max(myCoords2Shifted, axis=0)
                        midFaces2[idx2, 0] = 0.5*(limitsFaces2[idx2, 0] + limitsFaces2[idx2, 2]) # z coord mean
                        midFaces2[idx2, 1] = np.angle(np.exp(1j*limitsFaces2[idx2, 1])+np.exp(1j*limitsFaces2[idx2, 3])) # phi coord mean
                        if midFaces2[idx2, 1] < 0.:
                            midFaces2[idx2, 1] = midFaces2[idx2, 1] + 2*np.pi # correction to 0 ... 2pi
                        midFaces2Shifted[idx2, 0] = midFaces2[idx2, 0]
                        midFaces2Shifted[idx2, 1] = np.angle(np.exp(1j*limitsFaces2Shifted[idx2, 1])+np.exp(1j*limitsFaces2Shifted[idx2, 3])) # phi coord mean shifted
                        if midFaces2Shifted[idx2, 1] < 0.:
                            midFaces2Shifted[idx2, 1] = midFaces2Shifted[idx2, 1] + 2*np.pi # correction to 0 ... 2pi
                ### End of splitting ### 
                progWin = progressWindow(noOfTotalRelevantFaces1-1, 'Searching non-conform interfaces between block' + str(elems[blockCombi[0]].attrs['Id']) + ' and ' + str(elems[blockCombi[1]].attrs['Id']))
                myStringWrapped = ''
                for idx1 in range(len(limitsFaces1)): 
                    face1 = limitsFaces1[idx1]
                    #print('\n ### New hex element: ' + str(elems1[idx1,0]) + ' with limits: ' + str(face1))
                    partnerFace2 = np.invert(np.logical_or(np.logical_or(limitsFaces2[:,0]>face1[2], limitsFaces2[:,1]>face1[3]) , np.logical_or(limitsFaces2[:,2]<face1[0], limitsFaces2[:,3]<face1[1]))) # Check for elements outside limits; Invertion gives us the overlapping partners
                    partnerFace2Idx = np.where(partnerFace2)[0]
                    currentMidAngle = midFaces1[idx1][1]
                    wrap = 0
                    if (mode == "cylinder") and (abs(currentMidAngle-np.pi)>np.pi/2.): 
                        wrap = 1
                        face1Shifted = limitsFaces1Shifted[idx1]
                        # Additional check necessary due to angle wrapping (0=2pi yields fail of larger/smaller operator principle)
                        partnerFace2cylCheck = np.invert(np.logical_or(np.logical_or(limitsFaces2Shifted[:,0]>face1Shifted[2], limitsFaces2Shifted[:,1]>face1Shifted[3]) , np.logical_or(limitsFaces2Shifted[:,2]<face1Shifted[0], limitsFaces2Shifted[:,3]<face1Shifted[1]))) # Check for elements outside limits with 180 deg shift; Invertion gives us the overlapping partners
                        partnerFace2Idx = np.where(partnerFace2cylCheck)[0]
                        myStringWrapped = myStringWrapped + ' ' + str(elems1[idx1,0])
                    # Loop over potential partners
                    myPartnerString = ''
                    #print(len(partnerFace2Idx))
                    for idx2 in partnerFace2Idx: 
                        if (wrap) and (mode=='cylinder') and ((limitsFaces2Shifted[idx2][3] - limitsFaces2Shifted[idx2][1])>np.pi): # excluding shells, which again have the wrapping problem (min/max switched)
                            continue
                        if (wrap==0) and (mode=='cylinder') and ((limitsFaces2[idx2][3] - limitsFaces2[idx2][1])>np.pi): # excluding shells, which again have the wrapping problem (min/max switched)
                            continue
                        myPartnerString = myPartnerString + ' ' + str(elems2[idx2,0])
                        #print('# New Partner shell element: ' + str(elems2[idx2,0]))
                        if (wrap) and (mode=='cylinder'): 
                          localCommonLimits = [max([face1Shifted[0], limitsFaces2Shifted[idx2][0]]), max([face1Shifted[1], limitsFaces2Shifted[idx2][1]]), min([face1Shifted[2], limitsFaces2Shifted[idx2][2]]), min([face1Shifted[3], limitsFaces2Shifted[idx2][3]])]
                          area = abs(localCommonLimits[2]-localCommonLimits[0])*abs(localCommonLimits[3]-localCommonLimits[1])*surfaceRadius
                        else: 
                          localCommonLimits = [max([face1[0], limitsFaces2[idx2][0]]), max([face1[1], limitsFaces2[idx2][1]]), min([face1[2], limitsFaces2[idx2][2]]), min([face1[3], limitsFaces2[idx2][3]])]
                          area = abs(localCommonLimits[2]-localCommonLimits[0])*abs(localCommonLimits[3]-localCommonLimits[1])
                        # Skip this interface as area is almost zero
                        if area < tolerance:
                            continue 
                        # Compute new interface nodes
                        if mode == "plane": 
                            localMidX = 0.5*(localCommonLimits[0] + localCommonLimits[2]) # x coord mean
                            localMidY = 0.5*(localCommonLimits[1] + localCommonLimits[3]) # y coord mean
                            localInterNodeCoords = np.array([[localCommonLimits[0],localCommonLimits[1],0],[localCommonLimits[2],localCommonLimits[1],0],[localCommonLimits[2],localCommonLimits[3],0],[localCommonLimits[0],localCommonLimits[3],0],  # 4 edge nodes
                                                             [localMidX,localCommonLimits[1],0],           [localCommonLimits[2],localMidY,0],           [localMidX,localCommonLimits[3],0],           [localCommonLimits[0],localMidY,0], # 4 midside nodes 
                                                             [localMidX,localMidY,0]]) # 1 central node
                            globalInterNodeCoords = (Tinv @ localInterNodeCoords[:noOfFaceNodes,:].T).T + originRectangle1
                            # Compute local and global coords of pseudo matching nodes (required for integration / assembly)
                            localCoords1 = relevantNodes1Coords[idx1*4:(idx1*4+4),:]
                            localCoords2 = relevantNodes2Coords[idx2*4:(idx2*4+4),:]
                            globalCoords1 = (Tinv @ localCoords1.T).T + originRectangle1
                            globalCoords2 = (Tinv @ localCoords2.T).T + originRectangle1
                        elif mode == "cylinder": 
                            # Compute local and global coords of pseudo matching nodes (required for integration / assembly)
                            if wrap: 
                              localMidZ   = 0.5*(localCommonLimits[0] + localCommonLimits[2]) # z coord mean
                              localMidPhi = np.angle(np.exp(1j*localCommonLimits[1])+np.exp(1j*localCommonLimits[3])) # phi coord mean
                              localInterNodeCoords = np.array([[-1.*surfaceRadius*np.cos(localCommonLimits[1]),-1.*surfaceRadius*np.sin(localCommonLimits[1]),localCommonLimits[0]], # 4 edge nodes
                                                              [-1.*surfaceRadius*np.cos(localCommonLimits[1]),-1.*surfaceRadius*np.sin(localCommonLimits[1]),localCommonLimits[2]],
                                                              [-1.*surfaceRadius*np.cos(localCommonLimits[3]),-1.*surfaceRadius*np.sin(localCommonLimits[3]),localCommonLimits[2]],
                                                              [-1.*surfaceRadius*np.cos(localCommonLimits[3]),-1.*surfaceRadius*np.sin(localCommonLimits[3]),localCommonLimits[0]],
                                                              [-1.*surfaceRadius*np.cos(localCommonLimits[1]),-1.*surfaceRadius*np.sin(localCommonLimits[1]),localMidZ           ], # 4 midside nodes 
                                                              [-1.*surfaceRadius*np.cos(localMidPhi),         -1.*surfaceRadius*np.sin(localMidPhi),         localCommonLimits[2]],
                                                              [-1.*surfaceRadius*np.cos(localCommonLimits[3]),-1.*surfaceRadius*np.sin(localCommonLimits[3]),localMidZ           ],
                                                              [-1.*surfaceRadius*np.cos(localMidPhi),         -1.*surfaceRadius*np.sin(localMidPhi),         localCommonLimits[0]],
                                                              [-1.*surfaceRadius*np.cos(localMidPhi),         -1.*surfaceRadius*np.sin(localMidPhi),         localMidZ           ]]) # 1 central node
                              localCoords1 = np.array([relevantNodes1CartesianCoords[idx1*4:(idx1*4+4),2],relevantNodes1CylinderPhiShifted[idx1*4:(idx1*4+4)]]).T
                              localCoords2 = np.array([relevantNodes2CartesianCoords[idx2*4:(idx2*4+4),2],relevantNodes2CylinderPhiShifted[idx2*4:(idx2*4+4)]]).T
                            else: 
                              localMidZ   = 0.5*(localCommonLimits[0] + localCommonLimits[2]) # z coord mean
                              localMidPhi = np.angle(np.exp(1j*localCommonLimits[1])+np.exp(1j*localCommonLimits[3])) # phi coord mean
                              localInterNodeCoords = np.array([[surfaceRadius*np.cos(localCommonLimits[1]),surfaceRadius*np.sin(localCommonLimits[1]),localCommonLimits[0]], # 4 edge nodes
                                                              [surfaceRadius*np.cos(localCommonLimits[1]),surfaceRadius*np.sin(localCommonLimits[1]),localCommonLimits[2]],
                                                              [surfaceRadius*np.cos(localCommonLimits[3]),surfaceRadius*np.sin(localCommonLimits[3]),localCommonLimits[2]],
                                                              [surfaceRadius*np.cos(localCommonLimits[3]),surfaceRadius*np.sin(localCommonLimits[3]),localCommonLimits[0]],
                                                              [surfaceRadius*np.cos(localCommonLimits[1]),surfaceRadius*np.sin(localCommonLimits[1]),localMidZ           ], # 4 midside nodes 
                                                              [surfaceRadius*np.cos(localMidPhi),         surfaceRadius*np.sin(localMidPhi),         localCommonLimits[2]],
                                                              [surfaceRadius*np.cos(localCommonLimits[3]),surfaceRadius*np.sin(localCommonLimits[3]),localMidZ           ],
                                                              [surfaceRadius*np.cos(localMidPhi),         surfaceRadius*np.sin(localMidPhi),         localCommonLimits[0]],
                                                              [surfaceRadius*np.cos(localMidPhi),         surfaceRadius*np.sin(localMidPhi),         localMidZ           ]]) # 1 central node
                              localCoords1 = np.array([relevantNodes1CartesianCoords[idx1*4:(idx1*4+4),2],relevantNodes1CylinderPhi[idx1*4:(idx1*4+4)]]).T
                              localCoords2 = np.array([relevantNodes2CartesianCoords[idx2*4:(idx2*4+4),2],relevantNodes2CylinderPhi[idx2*4:(idx2*4+4)]]).T
                            globalInterNodeCoords = (Tinv @ localInterNodeCoords[:noOfFaceNodes,:].T).T + cylinderOrigin
                            globalCoords1 = (Tinv @ relevantNodes1CartesianCoords[idx1*4:(idx1*4+4),:].T).T + cylinderOrigin
                            globalCoords2 = (Tinv @ relevantNodes2CartesianCoords[idx2*4:(idx2*4+4),:].T).T + cylinderOrigin
                        if (wrap) and (mode=='cylinder'): 
                            smaller1 = localCoords1[:,:2] < midFaces1Shifted[idx1]
                            larger1 = localCoords1[:,:2] > midFaces1Shifted[idx1]
                            smaller2 = localCoords2[:,:2] < midFaces2Shifted[idx2]
                            larger2 = localCoords2[:,:2] > midFaces2Shifted[idx2]
                        else:
                            smaller1 = localCoords1[:,:2] < midFaces1[idx1]
                            larger1 = localCoords1[:,:2] > midFaces1[idx1]
                            smaller2 = localCoords2[:,:2] < midFaces2[idx2]
                            larger2 = localCoords2[:,:2] > midFaces2[idx2]
                        #
                        nodeIdxOrder1 = [ np.argwhere(np.multiply.reduce(smaller1, axis=1))[0][0], np.argwhere(smaller1[:,1]*larger1[:,0])[0][0], np.argwhere(np.multiply.reduce(larger1, axis=1))[0][0], np.argwhere(smaller1[:,0]*larger1[:,1])[0][0] ]
                        if nodeIdxOrder1 in [[0,1,2,3],[1,2,3,0],[2,3,0,1],[3,0,1,2]]:
                            nodeIdxOrder1 = nodeIdxOrder1 + [[4,5,6,7][nodeIdx] for nodeIdx in nodeIdxOrder1] + [8]
                        else: 
                            nodeIdxOrder1 = nodeIdxOrder1 + [[7,4,5,6][nodeIdx] for nodeIdx in nodeIdxOrder1] + [8]
                        pseudoMatchingNodes1 = [elems1[idx1,nodeIdx+1] for nodeIdx in nodeIdxOrder1[:noOfFaceNodes]]
                        #
                        nodeIdxOrder2 = [ np.argwhere(np.multiply.reduce(smaller2, axis=1))[0][0], np.argwhere(smaller2[:,1]*larger2[:,0])[0][0], np.argwhere(np.multiply.reduce(larger2, axis=1))[0][0], np.argwhere(smaller2[:,0]*larger2[:,1])[0][0] ]
                        if nodeIdxOrder2 in [[0,1,2,3],[1,2,3,0],[2,3,0,1],[3,0,1,2]]:
                            nodeIdxOrder2 = nodeIdxOrder2 + [[4,5,6,7][nodeIdx] for nodeIdx in nodeIdxOrder2] + [8]
                        else: 
                            nodeIdxOrder2 = nodeIdxOrder2 + [[7,4,5,6][nodeIdx] for nodeIdx in nodeIdxOrder2] + [8]
                        pseudoMatchingNodes2 = [elems2[idx2,nodeIdx+1] for nodeIdx in nodeIdxOrder2[:noOfFaceNodes]]
                        # Compute normal of elem 1 using original order 
                        a1 = [globalCoords1[1,0] - globalCoords1[0,0], globalCoords1[1,1] - globalCoords1[0,1], globalCoords1[1,2] - globalCoords1[0,2]] 
                        b1 = [globalCoords1[3,0] - globalCoords1[0,0], globalCoords1[3,1] - globalCoords1[0,1], globalCoords1[3,2] - globalCoords1[0,2]]
                        normal1 = np.cross(a1,b1)
                        normal1 = normal1 / np.linalg.norm(normal1)
                        # Compute normal of elem 2
                        a2 = [globalCoords2[1,0] - globalCoords2[0,0], globalCoords2[1,1] - globalCoords2[0,1], globalCoords2[1,2] - globalCoords2[0,2]] 
                        b2 = [globalCoords2[3,0] - globalCoords2[0,0], globalCoords2[3,1] - globalCoords2[0,1], globalCoords2[3,2] - globalCoords2[0,2]]
                        normal2 = np.cross(a2,b2)
                        normal2 = normal2 / np.linalg.norm(normal2)
                        # Identify orientation
                        cosineOfAngle = np.dot(normal1, normal2)
                        if cosineOfAngle > 0: # Normal vector show in equal direction
                            ori = -1
                        else:
                            ori = 1
                        # Save everything
                        foundNCInterFaceElements.append(NCinterfaceElement())
                        foundNCInterFaceElements[-1].ori = ori
                        [generatedInterNodesIds.append(np.uint64(nodeId + interNodesMaxId + interNodeCounter)) for nodeId in range(1,noOfFaceNodes+1)]
                        [generatedInterNodesCoords.append(list(coords)) for coords in globalInterNodeCoords]
                        foundNCInterFaceElements[-1].interNodes = [np.uint64(nodeId + interNodesMaxId + interNodeCounter) for nodeId in range(1,noOfFaceNodes+1)]
                        interNodeCounter += noOfFaceNodes
                        foundNCInterFaceElements[-1].fluidNodes = [np.uint64(nodeID) for nodeID in pseudoMatchingNodes1]
                        foundNCInterFaceElements[-1].structuralNodes = [np.uint64(nodeID) for nodeID in pseudoMatchingNodes2]
                        foundNCInterFaceElements[-1].fluidElemId = np.uint64(elems1[idx1,0])
                        foundNCInterFaceElements[-1].structElemId = np.uint64(elems2[idx2,0])
                        foundNCInterFaceElements[-1].fluidBlockIdx = blockCombi[0]
                        foundNCInterFaceElements[-1].structBlockIdx = blockCombi[1]
                    #print('Partners: Highlight element ' + myPartnerString)
                    progWin.setValue(idx1)
                    QApplication.processEvents()
                if foundNCInterFaceElements != []:
                    foundNCInterFaceElementsBlocks.append([foundNCInterFaceElements, generatedInterNodesIds, generatedInterNodesCoords])
    return foundNCInterFaceElementsBlocks

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

class NCinterfaceElement: # Define an interface element
    def __init__(self):
        self.Id = np.uint64(0)
        self.type = 'undefined'
        self.ori = np.int64(0)
        self.structBlockIdx = np.uint64(0)
        self.fluidBlockIdx = np.uint64(0)
        self.structElemId = np.uint64(0)
        self.fluidElemId = np.uint64(0)
        self.structuralNodes = []
        self.fluidNodes = []
        self.fluidMaterialId = np.uint64(0)
        self.structuralMaterialId = np.uint64(0)
        self.interNodes = []
        