"""
Created on September 20 2022

author: lukas outzen

------ Description ------
Script for setting up a predefined and automatic loadcreator execution.
The purpose of this is the ability to automatically convert cub5 files into hdf5 files,
to be able to run automated variations of geometry (and therefore mesh) variations.
The process steps, that are usually done in the GUI, are predefined in this script
and must be modified individually depending of the use case.

-------- Manual --------
To run the loadcreator software in the command line instead of a GUI, use the following command:

python3 .\main.py --cmd --script .\examples\scripts\modelscript_basic.py
           |        |        |        |
           |        |        |        Path to this file (script), in which the loadcreator run is specified.
           |        |        Flag for specifying that a script is used. Alteratively, use short form '-s'.
           |        Flag for entering the command line mode of the loadcreator software. Alternatively, use short form '-c'.
           Execute the loadcreator software.
"""

import os

##### Open cub5 file path #####
cub5_path = "R:/MS_2020_13_DFG_GRK_2075/Projektdaten/transmissibility_functions/data/simulation/simplebeam/simplebeam.cub5"                   # path to cub5 file (with forward slashes!)
tool.loadInput(cub5_path)                    

##### Specify frequency steps #####
tool.setFrequency(10, 1000, 10)                          # (min_freq, freq_steps, freq_delta)

##### Define load #####                         
tool.addLoad(
    'Point force',                                      # definition of load type (other types not yet implemented)
    ((0., 1., 0.),                                      # definition of point force magnitude (x_dir, y_dir, z_dir)
    1,))                                                # definition of point force nodeset

##### Define materials #####
tool.addMaterial(                                       
    'STRUCT linear visco iso',                          # material type
    [100.e9, 1, 0.01, 0.34, 0., 0., 0., 0., 2700., 0.]) # material parameters: ['E' , 'type', 'eta', 'nu',  'A',  'Ix',  'Iy',  'Iz', 'rho', 't']
tool.addMaterial(                                       
    'STRUCT linear visco iso',                          # material type
    [100.e9, 1, 0.01, 0.34, 0., 0., 0., 0., 2700., 0.])  # material parameters: ['E' , 'type', 'eta', 'nu',  'A',  'Ix',  'Iy',  'Iz', 'rho', 't']

##### Assign element type and materials to each block #####
tool.setBlockProperties({                               # For each block in geometry, define the following properties
    'Block_1': ('Brick8', 1, 'global'),                 # (Element type, material (number as defined above), orientation)
    'Block_2': ('Brick8', 2, 'global'),
})

##### Define constraints #####
tool.addConstraint(                                     
    'BC | Structure | Fieldvalue',                      # constraint type, DOF: ['u1', 'u2', 'u3', 'w1', 'w2', 'w3'] (u -> translational, w -> rotational)
    ((1 , 1 , 1 , 1 , 1 , 1 ),                          # constraint activation (0 -> DOF not constraint, 1 -> DOF constraint)
     (0., 0., 0., 0., 0., 0.),                          # constraint values
      2,))                                              # nodeset with constraint nodes

print(f'  > Script successfully run. The hdf5 file has been saved in {cub5_path[:-5]}.hdf5.')