### Details: cParserSalomeMed
### Date: 26.02.2024
### Author: Harikrishnan Sreekumar

# python modules
import numpy as np
#import meshio
from ThirdParty import meshio

# project imports
from modules.standardFunctionsGeneral import identifyElemType, createInitialBlockDataSet

#@brief Class to deal parsing of Salome med file
class cParserSalomeMed:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief read nodes directly from Salome med
    def readNodes(self, myModel):
        hdf5File = myModel.hdf5File

        meshMeds = meshio.read(self.filename)
        pts = []
        for meshMed in meshMeds:
            pts.append(np.array(meshMed.points)) # points
        pts = np.concatenate(pts,axis=0)
        
        g = hdf5File.create_group('Nodes')
        g = hdf5File.create_group('Nodesets')
        
        g = hdf5File['Nodes']
        comp_type = np.dtype([('Ids', 'i8'), ('xCoords', 'f8'), ('yCoords', 'f8'), ('zCoords', 'f8')])
        dataSet = g.create_dataset('mtxFemNodes', (pts.shape[0],), comp_type)
        dataSet[:,'Ids'] = np.arange(pts.shape[0])+1
        dataSet[:,'xCoords'] = pts[:,0]
        dataSet[:,'yCoords'] = pts[:,1]
        if pts.shape[1] == 3:
            dataSet[:,'zCoords'] = pts[:,2]
        else:
            dataSet[:,'zCoords'] = 0

        myModel.nodes = hdf5File['Nodes/mtxFemNodes']
        myModel.nodesInv = dict([[ID, n] for n, ID in enumerate(myModel.nodes[:,'Ids'])])
        
        # Nodesets 
        g = hdf5File['Nodesets']
        totalNodes = 0
        for meshMed in meshMeds:
            for id, every_key in enumerate(meshMed.point_tags):
                nodesetID = id + 1

                if every_key in meshMed.point_data["point_tags"]:
                    found_node_ids = np.argwhere(meshMed.point_data["point_tags"]==every_key) + 1 + totalNodes

                nodesetValue = found_node_ids.reshape(-1,1)
                g.create_dataset('vecNodeset' + str(nodesetID), data=nodesetValue)
                g['vecNodeset' + str(nodesetID)].attrs['Id'] = np.uint64(nodesetID)

            totalNodes += (np.size(meshMed.points,0))
        
        for nodeset in hdf5File['Nodesets'].keys():
            myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])

                
    # @brief read elements directly from Salome med
    def readElements(self, myModel):
        hdf5File = myModel.hdf5File

        meshMeds = meshio.read(self.filename)
        # the meshMed can be a list
        
        g = hdf5File.create_group('Elementsets')
        g = hdf5File.create_group('Elements')
        global_block_id = 0
        totalElem = 0
        totalNodes = 0
        for meshMed in meshMeds:
            cells = meshMed.cells
            for id, every_key in enumerate(meshMed.cell_tags): # iterate through groups
                elem = None
                for id_cell, every_mesh in enumerate(meshMed.cell_data["cell_tags"]): # find in mesh
                    valid_elem_connectivity = None
                    if every_key in every_mesh:
                        # contains valid elements
                        valid_cell = cells[id_cell].data
                        valid_elem_connectivity = np.array(valid_cell[every_mesh==every_key]) + 1

                        if elem is None:
                            elem = valid_elem_connectivity
                        else:
                            if elem.shape[1] != valid_elem_connectivity.shape[1]:
                                print('Element connectivity do not match')
                            
                            elem = np.concatenate((elem, valid_elem_connectivity), axis=0)
                totalNodesperBlock=np.max(elem.flatten())
                elem += totalNodes
                
                N = elem.shape[0]
                M = elem.shape[1]+1

                if elem.shape[1] == 2:
                    elemType = 'Pointmass'
                    elem = np.unique(np.ndarray.flatten(elem))
                    elem = np.ndarray.reshape(elem,[elem.shape[0],1])
                    N = elem.shape[0]
                    M = elem.shape[1]+1
                elif elem.shape[1] == 3:
                    #### ATTENTION: Only fix for CA Lab3
                    elemType = 'Pointmass'
                    elem = np.unique(np.ndarray.flatten(elem))
                    elem = np.ndarray.reshape(elem,[elem.shape[0],1])
                    N = elem.shape[0]
                    M = elem.shape[1]+1
                elif elem.shape[1] == 4:
                    elemType = 'DSG4'
                elif elem.shape[1] == 9:
                    elemType = 'DSG9'
                elif elem.shape[1] == 8:
                    elemType = 'Fluid8'
                    
                    elpasoElemConnectivity = np.zeros_like(elem)
                    elpasoElemConnectivity[:,0] = elem[:,0]
                    elpasoElemConnectivity[:,1] = elem[:,3]
                    elpasoElemConnectivity[:,2] = elem[:,2]
                    elpasoElemConnectivity[:,3] = elem[:,1]
                    
                    elpasoElemConnectivity[:,4] = elem[:,4]
                    elpasoElemConnectivity[:,5] = elem[:,7]
                    elpasoElemConnectivity[:,6] = elem[:,6]
                    elpasoElemConnectivity[:,7] = elem[:,5]
                    
                    elem = elpasoElemConnectivity                
                elif elem.shape[1] == 27:
                    elemType = 'Fluid27'
                    elpasoElemConnectivity = np.zeros_like(elem)
                    elpasoElemConnectivity[:,0] = elem[:,3]
                    elpasoElemConnectivity[:,1] = elem[:,7]
                    elpasoElemConnectivity[:,2] = elem[:,6]
                    elpasoElemConnectivity[:,3] = elem[:,2]
                    elpasoElemConnectivity[:,4] = elem[:,0]
                    elpasoElemConnectivity[:,5] = elem[:,4]
                    elpasoElemConnectivity[:,6] = elem[:,5]
                    elpasoElemConnectivity[:,7] = elem[:,1]
                    elpasoElemConnectivity[:,8] = elem[:,19]

                    elpasoElemConnectivity[:,9] = elem[:,14]
                    elpasoElemConnectivity[:,10] = elem[:,18]
                    elpasoElemConnectivity[:,11] = elem[:,10]
                    elpasoElemConnectivity[:,12] = elem[:,11]
                    elpasoElemConnectivity[:,13] = elem[:,15]
                    elpasoElemConnectivity[:,14] = elem[:,13]
                    elpasoElemConnectivity[:,15] = elem[:,9]
                    elpasoElemConnectivity[:,16] = elem[:,16]
                    elpasoElemConnectivity[:,17] = elem[:,12]

                    elpasoElemConnectivity[:,18] = elem[:,17]
                    elpasoElemConnectivity[:,19] = elem[:,8]
                    elpasoElemConnectivity[:,20] = elem[:,26]
                    elpasoElemConnectivity[:,21] = elem[:,23]
                    elpasoElemConnectivity[:,22] = elem[:,21]
                    elpasoElemConnectivity[:,23] = elem[:,20]
                    elpasoElemConnectivity[:,24] = elem[:,25]
                    elpasoElemConnectivity[:,25] = elem[:,24]
                    elpasoElemConnectivity[:,26] = elem[:,22]
                    
                    elem = elpasoElemConnectivity   

                dataSet = createInitialBlockDataSet(g, elemType, global_block_id+1, N, M)
                global_block_id += 1
                dataSet[:,0] = np.arange(elem.shape[0])+1+totalElem
                dataSet[:,1:] = elem
                
                myModel.elems.append(dataSet)
                totalElem += N
                
            # following total node update should be outside the single mesh loop
            totalNodes += totalNodesperBlock # increment only for multiple mesh med files because every mesh start with a form node id: 1

            for elemset in hdf5File['Elementsets'].keys():
                myModel.elementSets.append(hdf5File['Elementsets/' + elemset])

        
    # @brief Read setup from Salome med file
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