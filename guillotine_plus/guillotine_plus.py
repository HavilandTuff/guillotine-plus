#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guillotine-Plus: Efficient image slicing for GIMP 3.0

A GIMP plugin to slice images into predefined, evenly sized tiles,
with optional discardable divider lines.
"""

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk
import sys
import os

# Add lib directory to path for imports
plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

from lib.calculator import calculate_tile_regions, calculate_cut_lines
from lib.validator import validate_parameters
from lib.preview import create_preview_layer, draw_cut_lines, remove_preview_layer, find_preview_layer


class GuillotinePlus(Gimp.PlugIn):
    """Guillotine-Plus: Efficient image slicing for GIMP 3.0"""

    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return ["python-fu-guillotine-plus"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run,
            None
        )
        
        procedure.set_menu_label("Guillotine-Plus")
        procedure.add_menu_path("<Image>/Filters/Utils/")
        
        procedure.set_image_types("*")
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        
        procedure.set_documentation(
            "Slice image into tiles with dividers",
            "Efficiently slice images into predefined, evenly sized tiles, with optional discardable divider lines.",
            name
        )
        procedure.set_attribution("Antigravity & Karol", "Antigravity", "2026")
        
        # Add parameters
        procedure.add_int_argument(
            "tile-width",
            "Tile Width",
            "Width of each tile in pixels",
            1, 10000, 256,
            GObject.ParamFlags.READWRITE
        )
        
        procedure.add_int_argument(
            "tile-height",
            "Tile Height",
            "Height of each tile in pixels",
            1, 10000, 256,
            GObject.ParamFlags.READWRITE
        )
        
        procedure.add_int_argument(
            "divider-width",
            "Divider Width",
            "Width of discardable divider lines between tiles",
            0, 1000, 0,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, args, run_data):
        # Extract arguments
        tile_width = args.index(0)
        tile_height = args.index(1)
        divider_width = args.index(2)

        # Show dialog if interactive mode
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("guillotine-plus")
            dialog = GimpUi.ProcedureDialog.new(procedure, args, "Guillotine-Plus")
            dialog.fill(None)
            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            
            # Re-extract arguments after dialog (may have changed)
            tile_width = args.index(0)
            tile_height = args.index(1)
            divider_width = args.index(2)

        # Get image dimensions
        image_width = image.get_width()
        image_height = image.get_height()

        # Validate parameters
        is_valid, error_msg = validate_parameters(
            image_width, image_height,
            tile_width, tile_height, divider_width
        )
        
        if not is_valid:
            Gimp.message(f"Validation Error: {error_msg}")
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())

        # Start undo group
        image.undo_group_start()
        
        try:
            # Calculate tile regions
            tiles, metadata = calculate_tile_regions(
                image_width, image_height,
                tile_width, tile_height, divider_width
            )
            
            if not tiles:
                Gimp.message("No tiles could be created with the specified parameters.")
                return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
            
            # Calculate cut lines for preview
            vertical_lines, horizontal_lines = calculate_cut_lines(
                image_width, image_height,
                tile_width, tile_height, divider_width
            )
            
            # Remove existing preview layer if present
            existing_preview = find_preview_layer(image)
            if existing_preview:
                remove_preview_layer(image, existing_preview)
            
            # Create and draw preview
            preview_layer = create_preview_layer(image)
            if preview_layer:
                draw_cut_lines(image, preview_layer, vertical_lines, horizontal_lines)
            
            # Report results
            Gimp.message(
                f"Guillotine-Plus: Found {metadata['total_tiles']} tiles "
                f"({metadata['cols']} columns × {metadata['rows']} rows). "
                f"Preview layer created."
            )
            
        except Exception as e:
            Gimp.message(f"Error: {str(e)}")
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
        
        finally:
            image.undo_group_end()
            Gimp.displays_flush()
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())


if __name__ == "__main__":
    Gimp.main(GuillotinePlus.__gtype__, sys.argv)
