### Details: cParserGmsh
### Date: 26.02.2024
### Author: Harikrishnan Sreekumar

# python modules
import numpy as np
import h5py
import meshio

# project imports
from modules.standardFunctionsGeneral import identifyElemType, createInitialBlockDataSet

#@brief Class to deal parsing of Gmsh file
class cParserGmsh:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief read nodes directly from Gmsh hdf5
    def readNodes(self, myModel):
        hdf5File = myModel.hdf5File

        meshGmsh = meshio.read(self.filename)
        pts = np.array(meshGmsh.points) # points
        ########
        LoadPt=pts[0]
        pts= np.delete(pts,(0),axis=0)
        myID=np.where((np.abs(pts-LoadPt)<0.01).all(axis=1))
        myID=myID[0][0]+2 # add two because of index shift!
        ########
        
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
        for id, every_key in enumerate(meshGmsh.cell_sets):
            nodesetID = id + 1
            nodesetValue = np.unique(meshGmsh.cells_dict[list(meshGmsh.cell_sets_dict[every_key].keys())[0]]).reshape(-1,1)
            nodesetValue=nodesetValue+1
            ##########################
            if every_key=='LoadPt':
                nodesetValue=[[myID]]
            ##########################
            g.create_dataset('vecNodeset' + str(nodesetID), data=nodesetValue)
            g['vecNodeset' + str(nodesetID)].attrs['Id'] = np.uint64(nodesetID)
        
        for nodeset in hdf5File['Nodesets'].keys():
            myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])

                
    # @brief read elements directly from Gmsh hdf5
    def readElements(self, myModel):

    ###### so far only for one elemtype and block!!!!!!!!!!!!!!!!!!
    #### nodesets for bc and load
        hdf5File = myModel.hdf5File
        meshGmsh = meshio.read(self.filename)
        elem = np.array(meshGmsh.cells[-1].data)   # elements
        #elem = elem + 1 # zero based to one based
        
        g = hdf5File.create_group('Elements')
        N = elem.shape[0]
        M = elem.shape[1]+1

        if elem.shape[1] == 4:
            elemType = 'DSG4'
        elif elem.shape[1] == 9:
            elemType = 'DSG9'

        dataSet = createInitialBlockDataSet(g, elemType, 1, N, M)
        dataSet[:,0] = np.arange(elem.shape[0])+1
        dataSet[:,1:] = elem

        myModel.elems.append(dataSet)
        g = hdf5File.create_group('Elementsets')
        
    # @brief Read setup from Gmsh file
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