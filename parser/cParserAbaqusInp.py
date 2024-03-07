### Details: cParserAbaqusInp
### Date: 26.02.2024
### Author: Harikrishnan Sreekumar

# python modules
import numpy as np
import h5py
import meshio

# project imports
from modules.standardFunctionsGeneral import identifyElemType, createInitialBlockDataSet

#@brief Class to deal parsing of Abaqus Inp file
class cParserAbaqusInp:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief read nodes directly
    def readNodes(self, myModel):
        hdf5File = myModel.hdf5File

        meshAbaqus = meshio.read(self.filename)
        pts = np.array(meshAbaqus.points) # points
        
        g = hdf5File.create_group('Nodes')
        comp_type = np.dtype([('Ids', 'i8'), ('xCoords', 'f8'), ('yCoords', 'f8'), ('zCoords', 'f8')])
        dataSet = g.create_dataset('mtxFemNodes', (pts.shape[0],), comp_type)
        dataSet[:,'Ids'] = np.arange(pts.shape[0])+1
        dataSet[:,'xCoords'] = pts[:,0]
        dataSet[:,'yCoords'] = pts[:,1]
        dataSet[:,'zCoords'] = pts[:,2]

        myModel.nodes = hdf5File['Nodes/mtxFemNodes']
        myModel.nodesInv = dict([[ID, n] for n, ID in enumerate(myModel.nodes[:,'Ids'])])
        
        # Nodesets 
        g = hdf5File.create_group('Nodesets')
        for id, every_key in enumerate(meshAbaqus.point_sets):
            nodesetID = id + 1
            nodesetValue = np.array(meshAbaqus.point_sets[every_key]).reshape(-1,1)
            g.create_dataset('vecNodeset' + str(nodesetID), data=nodesetValue)
            g['vecNodeset' + str(nodesetID)].attrs['Id'] = np.uint64(nodesetID)
        
        for nodeset in hdf5File['Nodesets'].keys():
            myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])

                
    # @brief read elements directly
    def readElements(self, myModel):
        hdf5File = myModel.hdf5File

        meshAbaqus = meshio.read(self.filename)
        elem = np.array(meshAbaqus.cells[0].data)   # elements
        elem = elem + 1 # zero based to one based
        
        g = hdf5File.create_group('Elements')
        N = elem.shape[0]
        M = elem.shape[1]+1

        if elem.shape[1] == 4:
            elemType = 'DSG4'
        elif elem.shape[1] == 8:
            elemType = 'DSG8'

        dataSet = createInitialBlockDataSet(g, elemType, 1, N, M)
        dataSet[:,0] = np.arange(elem.shape[0])+1
        dataSet[:,1:] = elem

        myModel.elems.append(dataSet)
        
    # @brief Read setup
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