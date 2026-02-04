#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2026 HavilandTuff
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Guillotine-Plus: Efficient image slicing for GIMP 3.0
"""

import sys
import os


try:
    import gi
    gi.require_version('Gimp', '3.0')
    gi.require_version('GimpUi', '3.0')
    gi.require_version('Gegl', '0.4')
    from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk, Gegl
except Exception:
    pass

# Set up gplus_lib import path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)


try:
    from gplus_lib.calculator import calculate_tile_regions, calculate_cut_lines
    from gplus_lib.validator import validate_parameters
    from gplus_lib.preview import create_preview_layer, draw_cut_lines, remove_preview_layer, find_preview_layer
    from gplus_lib.slicer import slice_image, check_for_overwrites
    from gplus_lib.guide_manager import get_image_guides, calculate_guide_regions
except ImportError as e:
    pass

class GuillotinePlus(Gimp.PlugIn):
    def __init__(self):
        super().__init__()

    def do_query_procedures(self):
        return ["guillotine-plus-plugin"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        try:
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                self.run,
                None
            )

            procedure.set_menu_label("Guillotine-Plus")
            procedure.set_documentation(
                "Slice image into tiles with dividers", 
                "Efficiently slice images into predefined tiles with optional divider lines.", 
                name
            )
            procedure.set_attribution("Antigravity & Karol", "Antigravity", "2026")
            procedure.add_menu_path("<Image>/Filters/Utils/")
            
            procedure.set_image_types("*")
            procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
            
            
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
                "Width of discardable divider lines",
                0, 1000, 0,
                GObject.ParamFlags.READWRITE
            )

            # Slicing Method
            method_choice = Gimp.Choice.new()
            method_choice.add("grid", 0, "Fixed Grid", "")
            method_choice.add("guides", 1, "Use Guides", "")
            procedure.add_choice_argument(
                "slicing-method",
                "Slicing Method",
                "Choose between fixed grid or existing guides",
                method_choice,
                "grid", 
                GObject.ParamFlags.READWRITE
            )

            # Minimum Tile Size (for guides)
            procedure.add_int_argument(
                "min-tile-size",
                "Minimum Tile Size",
                "Ignore tiles smaller than this (in pixels, for Guide mode)",
                0, 10000, 0,
                GObject.ParamFlags.READWRITE
            )

            # Output directory
            procedure.add_file_argument(
                "output-directory",
                "Output Directory",
                "Directory where tiles will be saved",
                Gimp.FileChooserAction.SELECT_FOLDER,
                True, # none_ok
                None,
                GObject.ParamFlags.READWRITE
            )

            # Filename prefix
            procedure.add_string_argument(
                "filename-prefix",
                "Filename Prefix",
                "Prefix for output filenames",
                "tile",
                GObject.ParamFlags.READWRITE
            )

            # Output format
            format_choice = Gimp.Choice.new()
            format_choice.add("png", 0, "PNG", "")
            format_choice.add("jpg", 1, "JPEG", "")
            format_choice.add("webp", 2, "WebP", "")
            procedure.add_choice_argument(
                "output-format",
                "Output Format",
                "File format for sliced tiles",
                format_choice,
                "png",
                GObject.ParamFlags.READWRITE
            )

            # Execute mode
            mode_choice = Gimp.Choice.new()
            mode_choice.add("preview", 0, "Preview Only", "")
            mode_choice.add("slice", 1, "Slice and Save", "")
            procedure.add_choice_argument(
                "execute-mode",
                "Execute Mode",
                "Preview cut lines or perform actual slicing",
                mode_choice,
                "preview",
                GObject.ParamFlags.READWRITE
            )
            
            return procedure
        except Exception as e:
            # Re-raise to let GIMP know something went wrong
            raise e

    def run(self, procedure, run_mode, image, drawables, config, data):
        try:
            # Extract parameters from config
            tile_width = config.get_property("tile-width")
            tile_height = config.get_property("tile-height")
            divider_width = config.get_property("divider-width")
            output_dir_file = config.get_property("output-directory")
            prefix = config.get_property("filename-prefix")
            format_ext = config.get_property("output-format")
            execute_mode = config.get_property("execute-mode")
            slicing_method = config.get_property("slicing-method")
            min_tile_size = config.get_property("min-tile-size")
            
            

            if run_mode == Gimp.RunMode.INTERACTIVE:
                GimpUi.init("guillotine-plus")
                dialog = GimpUi.ProcedureDialog.new(procedure, config, "Guillotine-Plus")
                dialog.fill(None)
                
                if not dialog.run():
                    dialog.destroy()
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
                
                dialog.destroy()
                
                # Update values from dialog
                tile_width = config.get_property("tile-width")
                tile_height = config.get_property("tile-height")
                divider_width = config.get_property("divider-width")
                output_dir_file = config.get_property("output-directory")
                prefix = config.get_property("filename-prefix")
                format_ext = config.get_property("output-format")
                execute_mode = config.get_property("execute-mode")
                slicing_method = config.get_property("slicing-method")
                min_tile_size = config.get_property("min-tile-size")

            # Core logic execution
            image_width = image.get_width()
            image_height = image.get_height()
            
            # Calculation
            if slicing_method == "guides":
                v_guides, h_guides = get_image_guides(image)
                
                if not v_guides and not h_guides:
                    Gimp.message("Guillotine-Plus Warning: No guides found! Please add guides or switch to Grid mode.")
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error("No guides found"))
                    
                tiles, metadata = calculate_guide_regions(
                    image_width, image_height,
                    v_guides, h_guides,
                    min_size=min_tile_size
                )
            else:
                # Default: Grid mode
                # Validation (only needed for grid mode)
                is_valid, error_msg = validate_parameters(
                    image_width, image_height, 
                    tile_width, tile_height, divider_width
                )
                if not is_valid:
                    Gimp.message(f"Guillotine-Plus Error: {error_msg}")
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(error_msg))

                tiles, metadata = calculate_tile_regions(
                    image_width, image_height, 
                    tile_width, tile_height, divider_width
                )

            if execute_mode == "preview":
                # Preview logic
                v_lines, h_lines = calculate_cut_lines(
                    image_width, image_height, 
                    tile_width, tile_height, divider_width
                )
                
                image.undo_group_start()
                try:
                    existing = find_preview_layer(image)
                    if existing:
                        remove_preview_layer(image, existing)
                    
                    preview = create_preview_layer(image)
                    if preview:
                        draw_cut_lines(image, preview, v_lines, h_lines)
                    
                    Gimp.message(
                        f"Guillotine-Plus: Preview created for {metadata['total_tiles']} tiles "
                        f"({metadata['cols']} columns x {metadata['rows']} rows)."
                    )
                except Exception as e:
                    msg = f"Guillotine-Plus Preview Error: {str(e)}"
                    Gimp.message(msg)
                finally:
                    image.undo_group_end()
                    Gimp.displays_flush()
            else:
                # Execution mode: SLICE
                if not output_dir_file or not output_dir_file.get_path():
                    Gimp.message("Guillotine-Plus Error: No output directory selected.")
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error("No output directory"))

                # Perform slicing
                try:
                    count, paths = slice_image(
                        image, 
                        tiles, 
                        output_dir_file, 
                        prefix, 
                        format_ext
                    )
                    Gimp.message(f"Guillotine-Plus: Successfully saved {count} tiles to {output_dir_file.get_path()}")
                except Exception as e:
                    Gimp.message(f"Guillotine-Plus Slicing Error: {str(e)}")
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e)))

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)
        except Exception as e:
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e)))

if __name__ == "__main__":
    Gimp.main(GuillotinePlus.__gtype__, sys.argv)
