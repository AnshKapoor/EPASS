#########################################################
###                   Material-Tab                    ###
#########################################################

# Python 2.7.6

#########################################################
### Module Import                                     ###
from PyQt5.QtWidgets import QLineEdit
from materials import material
import numpy as np

#########################################################

#########################################################
### Material Widget for AF_LIN_UAF_ISO_DIR           ###
#########################################################

class AF_LIN_DAF_ISO_DIR(material):
    def __init__(self, Id):
        #
        self.type = 'AF_LIN_DAF_ISO_DIR'
        self.toolTip = '<b>Acoustic fluid damped material</b> <br>Basic material model for Helmholtz domain with constant damping.'
        #
        self.parameterNames =                              [ 'c' , 'rho', 't' , 'eta']
        self.parameterValues = [QLineEdit(str(x)) for x in [ 343.,  1.21,  0. , 0.001]]
        self.allowFrequencyDependentValues =               [False, False,False, False]
        self.parameterTipps = ['Speed of sound', 'Density', 'Thickness', 'Damping loss factor']
        [parameterValue.setToolTip(self.parameterTipps[n]) for n, parameterValue in enumerate(self.parameterValues)]
        #
        super(AF_LIN_DAF_ISO_DIR, self).__init__(Id)
        #

    def data2hdf5(self, materialsGroup): # Overriding method as parameter calculations are conducted and equivalent fluid material is used
        # Exporting the material
        set = materialsGroup.create_dataset('material' + self.Id.text(), data=[])
        set.attrs['Id'] = np.uint64(self.Id.text())
        set.attrs['MaterialType'] = 'AF_LIN_EQF_ISO_DIR'
        set.attrs['Name'] = self.name.text()
        cimag = np.imag(np.sqrt(float(self.parameterValues[0].text())**2 * (1+1j*float(self.parameterValues[3].text()))))
        newParameterNames  = [ 'cf'                           , 'rhof'                        , 't'                           , 'creal'                       , 'cimag', 'rhoreal'                     , 'rhoimag']
        newParameterValues = [ self.parameterValues[0].text() , self.parameterValues[1].text(), self.parameterValues[2].text(), self.parameterValues[0].text(), cimag  , self.parameterValues[1].text(), 0.]
        for n in range(len(newParameterNames)): 
            set.attrs[newParameterNames[n]] = float(newParameterValues[n])
