#############################################################
### Common standard functions for entire python framework ###
### without additional modules
#############################################################
#
from PyQt5.QtWidgets import QApplication
import numpy as np
from standardWidgets import progressWindow

# Read Nodes from cub5 and save them into hdf5 OR only read nodes directly from hdf5
def calcMeanSquared(hdf5ResultsFileStateGroup, fieldIndices, dB=1, ref=1.):
  noOfStateResults = len(hdf5ResultsFileStateGroup.keys())
  x = np.zeros((noOfStateResults), dtype=np.float)
  y = np.zeros((noOfStateResults), dtype=np.float)
  first = 1
  counter = 0
  progWin = progressWindow(noOfStateResults-1, 'Calculating mean squared values')
  for item in hdf5ResultsFileStateGroup.attrs.items():
    x[counter] = float(item[1])
    dataSet = hdf5ResultsFileStateGroup['vecFemStep' + str(int(item[0][8:])+1)]
    if first: 
      boolIdx = np.zeros((len(dataSet)), dtype=np.bool_)
      boolIdx[fieldIndices] = 1
      first = 0
    myArray = np.empty((len(fieldIndices)), dtype=np.complex)
    myArray.real = dataSet['real'][boolIdx]
    myArray.imag = dataSet['imag'][boolIdx]
    y[counter] = np.sum(np.power(np.abs(myArray),2)) / len(fieldIndices)
    counter = counter + 1
    progWin.setValue(counter)
    QApplication.processEvents()
  idx = np.argsort(x)
  if dB: 
    y = 10*np.log10(y/ref)
  return x[idx],y[idx]
    
        