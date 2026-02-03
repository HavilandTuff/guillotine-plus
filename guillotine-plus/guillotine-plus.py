#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk

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
        
        procedure.set_documentation(
            "Slice image into tiles with dividers",
            "Efficiently slice images into predefined, evenly sized tiles, with optional discardable divider lines.",
            name
        )
        procedure.set_attribution("Antigravity & Karol", "Antigravity", "2026")
        
        # Base arguments
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

        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, args, run_data):
        # Extract arguments
        tile_width = args.index(0)
        tile_height = args.index(1)
        divider_width = args.index(2)

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("guillotine-plus")
            dialog = GimpUi.ProcedureDialog.new(procedure, args, "Guillotine-Plus")
            dialog.fill(None)
            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())

        # Start undo group
        image.undo_group_start()
        
        try:
            Gimp.message(f"Guillotine-Plus: Ready to cut {tile_width}x{tile_height} tiles with {divider_width}px dividers.")
            # Implementation will go here in Phase 2 & 3
            
        except Exception as e:
            Gimp.message(f"Error: {str(e)}")
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
        
        finally:
            image.undo_group_end()
            Gimp.displays_flush()
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

Gimp.main(GuillotinePlus.__gtype__, __file__)
