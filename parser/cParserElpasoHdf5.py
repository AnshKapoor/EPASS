### Details: cParserElpasoHdf5
### Date: 26.02.2024
### Author: Christopher Blech, refactored by Harikrishnan Sreekumar

# python modules
import numpy as np
import h5py

# project imports

#@brief Class to deal parsing of elPaSo hdf5 file
class cParserElpasoHdf5:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief Read Nodes from cub5 and save them into hdf5 OR only read nodes directly from hdf5
    def readNodes(self, myModel):
        hdf5File = h5py.File(self.filename, 'r')

        myModel.nodes = hdf5File['Nodes/mtxFemNodes']
        myModel.nodesInv = dict([[ID, n] for n, ID in enumerate(myModel.nodes[:,'Ids'])])

        for nodeset in hdf5File['Nodesets'].keys():
            myModel.nodeSets.append(hdf5File['Nodesets/' + nodeset])
                
    # @brief Read Elements from cub5 and save them into hdf5 OR only read elements directly from hdf5
    def readElements(self, myModel):
        hdf5File = h5py.File(self.filename, 'r')

        for block in hdf5File['Elements'].keys():
            myModel.elems.append(hdf5File['Elements/' + block])

        for elemset in hdf5File['Elementsets'].keys():
            myModel.elementSets.append(hdf5File['Elementsets/' + elemset])

    # @brief Read setup from hdf5 file
    def readSetup(self, myModel):
        hdf5File = h5py.File(self.filename, 'r')

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