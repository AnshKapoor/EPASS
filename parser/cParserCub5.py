### Details: cParserCub5
### Date: 26.02.2024
### Author: Christopher Blech, refactored by Harikrishnan Sreekumar

# python modules
from PyQt5.QtWidgets import QApplication
import numpy as np
import h5py

# project imports
from standardWidgets import progressWindow, messageboxOK
from modules.standardFunctionsGeneral import identifyElemType, createInitialBlockDataSet


#@brief Class to deal parsing of Coreform Cubit Cub5 file
class cParserCub5:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief Read Nodes from cub5 and save them into hdf5
    def readNodes(self, myModel):
        hdf5File = myModel.hdf5File
        cub5File = h5py.File(self.filename,'r')

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
        
        for nodeset in hdf5File['Nodesets'].keys():
            myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])
            
    # @brief Read Elements from cub5 and save them into hdf5
    def readElements(self, myModel):
        hdf5File = myModel.hdf5File
        cub5File = h5py.File(self.filename,'r')

        myModel.allUsedNodes = []
        g = hdf5File.create_group('Elements')
        # Prepare dictionary for faster elem id search
        maxElemID = 0
        for coreformKey in cub5File['Mesh/Elements'].keys():
            myModel.elemsInvTags.append(coreformKey)
            # In the provided code snippet, `elemIDs` is being used to store the element IDs extracted
            # from the Cub5 file. These IDs are then used for various purposes such as identifying
            # elements, creating datasets, and processing element connectivity information. The
            # `elemIDs` variable is used in conjunction with other data structures and functions to
            # handle elements in the Cub5 file during the parsing process.
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

        for elemset in hdf5File['Elementsets'].keys():
            myModel.elementSets.append(hdf5File['Elementsets/' + elemset])
            
    # @brief Read setup from hdf5 file
    def readSetup(self, myModel):
        hdf5File = myModel.hdf5File

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