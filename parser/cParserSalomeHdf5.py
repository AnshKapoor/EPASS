### Details: cParserSalomeHdf5
### Date: 26.02.2024
### Author: Harikrishnan Sreekumar

# python modules
import numpy as np
import h5py

# project imports

#@brief Class to deal parsing of Salome hdf5 file
class cParserSalomeHdf5:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief read nodes directly from Salome hdf5
    def readNodes(self, myModel):
        print('! not implemented')
                
    # @brief read elements directly from Salome hdf5
    def readElements(self, myModel):
        print('! not implemented')
        
    # @brief Read setup from Salome hdf5 file
    def readSetup(self, myModel):
        print('! not implemented')