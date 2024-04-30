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

        meshMed = meshio.read(self.filename)
        pts = np.array(meshMed.points) # points
        
        g = hdf5File.create_group('Nodes')
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
        g = hdf5File.create_group('Nodesets')
        for id, every_key in enumerate(meshMed.point_tags):
            nodesetID = id + 1

            if every_key in meshMed.point_data["point_tags"]:
                found_node_ids = np.argwhere(meshMed.point_data["point_tags"]==every_key) +1

            nodesetValue = found_node_ids.reshape(-1,1)
            g.create_dataset('vecNodeset' + str(nodesetID), data=nodesetValue)
            g['vecNodeset' + str(nodesetID)].attrs['Id'] = np.uint64(nodesetID)
        
        for nodeset in hdf5File['Nodesets'].keys():
            myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])

                
    # @brief read elements directly from Salome med
    def readElements(self, myModel):
        hdf5File = myModel.hdf5File

        meshMed = meshio.read(self.filename)

        cells = meshMed.cells
        g = hdf5File.create_group('Elements')
        totalElem = 0
        for id, every_key in enumerate(meshMed.cell_tags):
            elem = None
            for id_cell, every_mesh in enumerate(meshMed.cell_data["cell_tags"]):
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

            N = elem.shape[0]
            M = elem.shape[1]+1

            if elem.shape[1] == 4:
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

            dataSet = createInitialBlockDataSet(g, elemType, id+1, N, M)
            dataSet[:,0] = np.arange(elem.shape[0])+1+totalElem
            dataSet[:,1:] = elem

            myModel.elems.append(dataSet)
            totalElem += N

        
        g = hdf5File.create_group('Elementsets')
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