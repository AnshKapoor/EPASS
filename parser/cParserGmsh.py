### Details: cParserGmsh
### Date: 26.02.2024
### Author: Harikrishnan Sreekumar

# python modules
import numpy as np
import h5py

# project imports

#@brief Class to deal parsing of Gmsh file
class cParserGmsh:
    def __init__(self, filename) -> None:
        self.filename = filename

    # @brief read nodes directly from Gmsh hdf5
    def readNodes(self, myModel):
        print('! not implemented')
                
    # @brief read elements directly from Gmsh hdf5
    def readElements(self, myModel):
        print('! not implemented')
        
    # @brief Read setup from Gmsh file
    def readSetup(self, myModel):
        print('! not implemented')