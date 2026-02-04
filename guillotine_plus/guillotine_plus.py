#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guillotine-Plus: Efficient image slicing for GIMP 3.0
"""

import sys
import os
import time

# Debug logging setup - MOVED TO TOP
ENABLE_DEBUG_LOGGING = False
LOG_FILE = "/tmp/guillotine_plus_debug.log"

def log_debug(message):
    if ENABLE_DEBUG_LOGGING:
        try:
            with open(LOG_FILE, "a") as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass 

log_debug("Guillotine-Plus script starting...")

try:
    import gi
    log_debug("Imported gi")
    gi.require_version('Gimp', '3.0')
    log_debug("Required Gimp 3.0")
    gi.require_version('GimpUi', '3.0')
    log_debug("Required GimpUi 3.0")
    gi.require_version('Gegl', '0.4')
    log_debug("Required Gegl 0.4")
    from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk, Gegl
    log_debug("Imported GObject/Gimp repositories")
except Exception as e:
    log_debug(f"CRITICAL IMPORT ERROR: {e}")
    # We continue, but it will likely fail later if these are missing.
    # However, for debugging, knowing WHICH one failed is key.

# Set up gplus_lib import path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

log_debug(f"Plugin directory: {plugin_dir}")
log_debug("Attempting to import gplus_lib...")

try:
    from gplus_lib.calculator import calculate_tile_regions, calculate_cut_lines
    log_debug("Imported calculator")
    from gplus_lib.validator import validate_parameters
    log_debug("Imported validator")
    from gplus_lib.preview import create_preview_layer, draw_cut_lines, remove_preview_layer, find_preview_layer
    log_debug("Imported preview")
    from gplus_lib.slicer import slice_image, check_for_overwrites
    log_debug("Imported slicer")
    from gplus_lib.guide_manager import get_image_guides, calculate_guide_regions
    log_debug("Imported guide manager")
except ImportError as e:
    log_debug(f"Library import error: {e}")
    pass
except Exception as e:
    log_debug(f"Unexpected error during import: {e}")

log_debug("Defining GuillotinePlus class...")


class GuillotinePlus(Gimp.PlugIn):
    def __init__(self):
        log_debug("GuillotinePlus initialized")
        super().__init__()

    def do_query_procedures(self):
        log_debug("Querying procedures")
        return ["guillotine-plus-plugin"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        log_debug(f"Creating procedure: {name}")
        try:
            procedure = Gimp.ImageProcedure.new(
                self,
                name,
                Gimp.PDBProcType.PLUGIN,
                self.run,
                None
            )
            
            log_debug(f"Procedure type: {type(procedure)}")

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
            
            # Add parameters using add_int_argument (reverting to check if it works)
            log_debug("Adding arguments...")
            
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
            
            log_debug("Procedure created successfully")
            return procedure
        except Exception as e:
            log_debug(f"Error creating procedure: {str(e)}")
            # Re-raise to let GIMP know something went wrong
            raise e

    def run(self, procedure, run_mode, image, drawables, config, data):
        log_debug(f"Running procedure with mode: {run_mode}")
        try:
            # Extract parameters from config using the modern property access
            tile_width = config.get_property("tile-width")
            tile_height = config.get_property("tile-height")
            divider_width = config.get_property("divider-width")
            output_dir_file = config.get_property("output-directory")
            prefix = config.get_property("filename-prefix")
            format_ext = config.get_property("output-format")
            execute_mode = config.get_property("execute-mode")
            slicing_method = config.get_property("slicing-method")
            min_tile_size = config.get_property("min-tile-size")
            
            log_debug(f"Parameters: method={slicing_method}, w={tile_width}, h={tile_height}, mode={execute_mode}")

            if run_mode == Gimp.RunMode.INTERACTIVE:
                GimpUi.init("guillotine-plus")
                dialog = GimpUi.ProcedureDialog.new(procedure, config, "Guillotine-Plus")
                dialog.fill(None)
                
                if not dialog.run():
                    dialog.destroy()
                    return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
                
                dialog.destroy()
                
                # Re-get values as they are updated by the dialog
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
            
            # 1. Calculate regions
            if slicing_method == "guides":
                log_debug("Using Guide-based slicing method")
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
                    # 2. Manage preview layer
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
                    log_debug(msg)
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
                        format_ext, 
                        log_debug
                    )
                    Gimp.message(f"Guillotine-Plus: Successfully saved {count} tiles to {output_dir_file.get_path()}")
                except Exception as e:
                    msg = f"Guillotine-Plus Slicing Error: {str(e)}"
                    log_debug(msg)
                    import traceback
                    log_debug(traceback.format_exc())
                    Gimp.message(msg)
                    return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(msg))

            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, None)
        except Exception as e:
            log_debug(f"Critical error in run loop: {e}")
            import traceback
            log_debug(traceback.format_exc())
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e)))

if __name__ == "__main__":
    log_debug("Starting Gimp.main...")
    log_debug(f"sys.argv: {sys.argv}")
    try:
        Gimp.main(GuillotinePlus.__gtype__, sys.argv)
        log_debug("Gimp.main returned (unexpected)")
    except Exception as e:
        log_debug(f"Error in Gimp.main: {e}")
