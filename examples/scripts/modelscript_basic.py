## usage: python3 .\main.py --cmd --script .\examples\scripts\modelscript_basic.py

tool.loadInput('./Plate_Shell4_Free_on_all_sides.cub5')
tool.setFrequency(9, 999, 99)
tool.addLoad('Point force', [9., 9., 9., 1])
#tool.addMaterial()
#tool.assignMaterialToBlock()
#tool.assignElementToBlock()
#tool.addConstraint()