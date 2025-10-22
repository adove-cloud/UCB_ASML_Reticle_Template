# UCB_ASML_Reticle_Template
Template files and python code to combine an individual's GDS file with UC Berkeley's Marvell Nanofabrication Lab's ASML reticle template file.

Python code requires gdstk package (minimum level 0.9.61) to execute.

- Python code will check the layers in the template file and in the design file and remap the template file layer to a new layer to avoid conflicts.
- Will ask whether your design is at reticle scale or wafer scale; will scale automatically if at wafer scale
- Will center design at (0,0)
- Will ask if this pattern will be made on NanoLab's mla150; will automatically left-right flip if so
