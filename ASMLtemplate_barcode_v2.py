#!/usr/bin/env python
# coding: utf-8

import gdstk
import math
import sys
from datetime import datetime
from packaging.version import parse as parse_version

# --- Version Check ---
MIN_GDSTK_VERSION = "0.9.61"
if parse_version(gdstk.__version__) < parse_version(MIN_GDSTK_VERSION):
    print(f"Error: Your gdstk version ({gdstk.__version__}) is too old.")
    print(f"Please upgrade to version {MIN_GDSTK_VERSION} or newer to run this script.")
    print("You can upgrade by running: pip install --upgrade gdstk")
    sys.exit(1)

# --- Custom Exception Classes ---

class InvalidBarcodeLength(Exception):
    """Exception raised if Barcode length is smaller than 1 or longer than 12 characters."""
    def __init__(self, barcode, message='Barcode must be between 1 and 12 characters long'):
        self.barcode = barcode
        self.message = message
        super().__init__(self.message)

class InvalidBarcodeCharacter(Exception):
    """Exception raised if there is a character in the barcode label that is not in the allowed list."""
    def __init__(self, character, message='Invalid Character in the Barcode String'):
        self.character = character
        self.message = message
        super().__init__(f"{message}: '{character}'")

# --- Barcode Constants and Dictionary ---

scale = 1e3
x0 = 69 * scale
y = (29.15 + 48.3 / 2) * scale
barheight = 5 * scale
quiet_zone = 8 * scale
x0_hrc = -69.5 * scale
y1_hrc = 37.5 * scale
y2_hrc = -37.5 * scale
wb = 0.450 * scale
ns = -0.200 * scale
nb = 0.200 * scale
ws = -0.450 * scale

startstop = [nb, ws, nb, ns, wb, ns, wb, ns, nb, ns]
codedict = {
    "A": [wb, ns, nb, ns, nb, ws, nb, ns, wb, ns], "B": [nb, ns, wb, ns, nb, ws, nb, ns, wb, ns],
    "C": [wb, ns, wb, ns, nb, ws, nb, ns, nb, ns], "D": [nb, ns, nb, ns, wb, ws, nb, ns, wb, ns],
    "E": [wb, ns, nb, ns, wb, ws, nb, ns, nb, ns], "F": [nb, ns, wb, ns, wb, ws, nb, ns, nb, ns],
    "G": [nb, ns, nb, ns, nb, ws, wb, ns, wb, ns], "H": [wb, ns, nb, ns, nb, ws, wb, ns, nb, ns],
    "I": [nb, ns, wb, ns, nb, ws, wb, ns, nb, ns], "J": [nb, ns, nb, ns, wb, ws, wb, ns, nb, ns],
    "K": [wb, ns, nb, ns, nb, ns, nb, ws, wb, ns], "L": [nb, ns, wb, ns, nb, ns, nb, ws, wb, ns],
    "M": [wb, ns, wb, ns, nb, ns, nb, ws, nb, ns], "N": [nb, ns, nb, ns, wb, ns, nb, ws, wb, ns],
    "O": [wb, ns, nb, ns, wb, ns, nb, ws, nb, ns], "P": [nb, ns, wb, ns, wb, ns, nb, ws, nb, ns],
    "Q": [nb, ns, nb, ns, nb, ns, wb, ws, wb, ns], "R": [wb, ns, nb, ns, nb, ns, wb, ws, nb, ns],
    "S": [nb, ns, wb, ns, nb, ns, wb, ws, nb, ns], "T": [nb, ns, nb, ns, wb, ns, wb, ws, nb, ns],
    "U": [wb, ws, nb, ns, nb, ns, nb, ns, wb, ns], "V": [nb, ws, wb, ns, nb, ns, nb, ns, wb, ns],
    "W": [wb, ws, wb, ns, nb, ns, nb, ns, nb, ns], "X": [nb, ws, nb, ns, wb, ns, nb, ns, wb, ns],
    "Y": [wb, ws, nb, ns, wb, ns, nb, ns, nb, ns], "Z": [nb, ws, wb, ns, wb, ns, nb, ns, nb, ns],
    "1": [wb, ns, nb, ws, nb, ns, nb, ns, wb, ns], "2": [nb, ns, wb, ws, nb, ns, nb, ns, wb, ns],
    "3": [wb, ns, wb, ws, nb, ns, nb, ns, nb, ns], "4": [nb, ns, nb, ws, wb, ns, nb, ns, wb, ns],
    "5": [wb, ns, nb, ws, wb, ns, nb, ns, nb, ns], "6": [nb, ns, wb, ws, wb, ns, nb, ns, nb, ns],
    "7": [nb, ns, nb, ws, nb, ns, wb, ns, wb, ns], "8": [wb, ns, nb, ws, nb, ns, wb, ns, nb, ns],
    "9": [nb, ns, wb, ws, nb, ns, wb, ns, nb, ns], "0": [nb, ns, nb, ws, wb, ns, wb, ns, nb, ns],
    "-": [nb, ws, nb, ns, nb, ns, wb, ns, wb, ns], ".": [wb, ws, nb, ns, nb, ns, wb, ns, nb, ns],
    "$": [nb, ws, nb, ws, nb, ws, nb, ns, nb, ns], "/": [nb, ws, nb, ws, nb, ns, nb, ws, nb, ns],
    "+": [nb, ws, nb, ns, nb, ws, nb, ws, nb, ns], "%": [nb, ns, nb, ws, nb, ws, nb, ws, nb, ns],
    " ": [nb, ws, wb, ns, nb, ns, wb, ns, nb, ns]}

# --- GDS Cell Creation Functions ---

def str2code(str2wrt):
    barcode = []
    barcode.extend(startstop)
    for char in str2wrt:
        barcode.extend(codedict[char])
    barcode.extend(startstop)
    return barcode

def barcad(barcode, lib_ref, layer_num, datatype_num=0):
    code_cell = lib_ref.new_cell('BARCODE')
    xcurr = 0
    for x in barcode:
        if x > 0:
            code_cell.add(gdstk.rectangle((xcurr, -barheight / 2), (xcurr + x, barheight / 2), layer=layer_num, datatype=datatype_num))
        xcurr += abs(x)
    return code_cell

def datecad(lib_ref, layer_num, datatype_num=0):
    date_cell = lib_ref.new_cell('DATE')
    today_text = gdstk.text(datetime.today().strftime('%Y-%m-%d'), 4 * scale, (0, 0), layer=layer_num, datatype=datatype_num)
    if today_text:
        (min_x, min_y), (max_x, max_y) = today_text[0].bounding_box()
        for poly in today_text[1:]:
            (bb_min_x, bb_min_y), (bb_max_x, bb_max_y) = poly.bounding_box()
            min_x, min_y = min(min_x, bb_min_x), min(min_y, bb_min_y)
            max_x, max_y = max(max_x, bb_max_x), max(max_y, bb_max_y)
        center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
        for poly in today_text:
            poly.translate(-center_x, -center_y)
    date_cell.add(*today_text)
    return date_cell

def humancad(str2wrt, lib_ref, layer_num, datatype_num=0):
    label_cell = lib_ref.new_cell('RETICLELABEL')
    text = gdstk.text(str2wrt, 4 * scale, (0, 0), layer=layer_num, datatype=datatype_num)
    if text:
        (min_x, min_y), (max_x, max_y) = text[0].bounding_box()
        for poly in text[1:]:
            (bb_min_x, bb_min_y), (bb_max_x, bb_max_y) = poly.bounding_box()
            min_x, min_y = min(min_x, bb_min_x), min(min_y, bb_min_y)
            max_x, max_y = max(max_x, bb_max_x), max(max_y, bb_max_y)
        center_x, center_y = (min_x + max_x) / 2, (min_y + max_y) / 2
        for poly in text:
            poly.translate(-center_x, -center_y)
    label_cell.add(*text)
    return label_cell

# --- Main Execution Block ---

if __name__ == "__main__":
    print("--- ASML Reticle Merge and Barcode Generator ---")

    while True:
        template_gds_file = input("Enter the name of the ASML template GDS file: ")
        try:
            template_lib = gdstk.read_gds(template_gds_file)
            print(f"Successfully loaded template '{template_gds_file}'.")
            break
        except FileNotFoundError:
            print(f"Error: The file '{template_gds_file}' was not found. Please try again.")

    while True:
        user_gds_file = input("Enter the name of your personal design GDS file: ")
        try:
            user_lib = gdstk.read_gds(user_gds_file)
            print(f"Successfully loaded your design '{user_gds_file}'.")
            break
        except FileNotFoundError:
            print(f"Error: The file '{user_gds_file}' was not found. Please try again.")

    # --- Layer Conflict Resolution ---
    user_layers_datatypes = user_lib.layers_and_datatypes()
    template_layers_datatypes = template_lib.layers_and_datatypes()
    
    barcode_layer_datatype = (4, 0)
    all_template_layers_datatypes = template_layers_datatypes.union({barcode_layer_datatype})
    
    conflicts = user_layers_datatypes.intersection(all_template_layers_datatypes)

    if conflicts:
        user_layers = {layer for layer, dt in user_layers_datatypes}
        max_user_layer = max(user_layers) if user_layers else 0
        new_layer = max_user_layer + 1
        print(f"\n! Layer conflict detected. Conflicting (layer, datatype) pairs: {conflicts}.")
        print(f"  All template and barcode features will be moved to a new, safe layer: {new_layer}")
        
        remap_dict = {
            old_ld: (new_layer, old_ld[1]) for old_ld in all_template_layers_datatypes
        }
        template_lib.remap(remap_dict)
        
        barcode_target_layer = new_layer
    else:
        print("\nNo layer conflicts detected.")
        barcode_target_layer = barcode_layer_datatype[0]

    # --- Cell Selection and Merging ---
    user_top_cells = [cell for cell in user_lib.top_level() if cell.name != '$$$CONTEXT_INFO$$$']
    if not user_top_cells:
        print("Error: No valid top-level cell found. Exiting.")
        exit()
    elif len(user_top_cells) == 1:
        user_cell_to_merge = user_top_cells[0]
        print(f"Using top-level cell: '{user_cell_to_merge.name}'")
    else:
        print("\nMultiple top-level cells found. Please choose one:")
        for i, cell in enumerate(user_top_cells):
            print(f"  {i+1}: {cell.name}")
        while True:
            try:
                choice = int(input(f"Enter number of the cell to merge (1-{len(user_top_cells)}): "))
                if 1 <= choice <= len(user_top_cells):
                    user_cell_to_merge = user_top_cells[choice - 1]
                    break
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
    # --- Scaling Factor Input ---
    scale_factor = 1.0
    while True:
        scale_input = input("\nIs your design at [w]afer scale or [r]eticle scale? (w/r): ").lower()
        if scale_input in ['w', 'wafer']:
            scale_factor = 4.0
            print("Applying 4x magnification for wafer scale.")
            break
        elif scale_input in ['r', 'reticle']:
            scale_factor = 1.0
            print("Applying 1x magnification for reticle scale.")
            break
        else:
            print("Invalid input. Please enter 'w' or 'r'.")

    design_cell_name = 'asml_template'
    template_cell_names = [c.name for c in template_lib.cells]
    if design_cell_name not in template_cell_names:
        print(f"Error: Template missing required cell '{design_cell_name}'.")
        exit()
    
    design_cell = template_lib[design_cell_name]
    template_lib.add(*user_lib.cells)
    
    cell_ref = gdstk.Reference(user_cell_to_merge.name, magnification=scale_factor)
    design_cell.add(cell_ref)
    print(f"Successfully added a {scale_factor}x reference to '{user_cell_to_merge.name}' into '{design_cell_name}'.")

    # --- Barcode Input and Creation ---
    while True:
        try:
            barcode_label = input("\nEnter barcode (1-12 alphanumeric characters): ").upper()
            if not 1 <= len(barcode_label) <= 12:
                raise InvalidBarcodeLength(barcode_label)
            if not all(char in codedict for char in barcode_label):
                invalid_char = next(char for char in barcode_label if char not in codedict)
                raise InvalidBarcodeCharacter(invalid_char)
            print(f"Barcode '{barcode_label}' is valid.")
            break
        except (InvalidBarcodeLength, InvalidBarcodeCharacter) as e:
            print(f"Error: {e}. Please use only A-Z, 0-9, and the characters: - . $ / + %")

    output_gds_file = input("\nEnter name for the final output file (e.g., 'merged.gds'): ")
    if not output_gds_file.lower().endswith('.gds'):
        output_gds_file += '.gds'

    barcode_cell = barcad(str2code(barcode_label), template_lib, barcode_target_layer)
    hrc_label_cell = humancad(barcode_label, template_lib, barcode_target_layer)
    date_cell = datecad(template_lib, barcode_target_layer)

    design_cell.add(gdstk.Reference(barcode_cell, (x0, y - quiet_zone), rotation=-math.pi / 2))
    design_cell.add(gdstk.Reference(hrc_label_cell, (x0_hrc, y2_hrc), rotation=math.pi / 2))
    design_cell.add(gdstk.Reference(date_cell, (x0_hrc, y1_hrc), rotation=math.pi / 2))
    print(f"\nBarcode and HRCs added to cell '{design_cell_name}'.")

    # --- Final MLA150 Transformation Step ---
    while True:
        mla_input = input("\nWill this design be fabricated on the Nanolab's MLA150? (y/n): ").lower()
        if mla_input in ['y', 'yes']:
            print("Creating 'for_the_mla' cell with required transformations.")
            mla_cell = template_lib.new_cell('for_the_mla')
            # Add a reference to 'asml_template' that is mirrored and rotated
            mla_ref = gdstk.Reference(design_cell, rotation=math.pi, x_reflection=True)
            mla_cell.add(mla_ref)
            print("MLA150-specific cell has been created.")
            break
        elif mla_input in ['n', 'no']:
            print("Skipping MLA150-specific transformation.")
            break
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            
    # --- Final File Write ---
    try:
        template_lib.write_gds(output_gds_file)
        print(f"\nSuccessfully saved final design to '{output_gds_file}'.")
    except Exception as e:
        print(f"An error occurred while saving: {e}")