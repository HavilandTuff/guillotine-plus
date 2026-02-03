---
name: gimp_3_0_python_plugin_dev
description: Expert GIMP 3.0 Python plugin development using GObject Introspection and the modern ProcedureConfig pattern.
---

# GIMP 3.0 Python Plugin Development

This guide focuses on the modern **Python 3** and **GObject Introspection (GI)** API for GIMP 3.0.

> [!IMPORTANT]
> GIMP 3.0 is a complete departure from GIMP 2.10. It uses Python 3, GTK 3, and GEGL. The old `gimpfu` module is gone.

## 1. Project Architecture

GIMP 3.0 strictly requires each plugin to live in its own directory. The directory name must match the main script name.

```text
~/.config/GIMP/3.0/plug-ins/
└── my-cool-plugin/                 # Directory name
    ├── my-cool-plugin.py           # Script name MUST match directory
    └── lib/                        # Sub-packages (optional)
        └── helper.py
```

### Folder Locations
- **Linux**: `~/.config/GIMP/3.0/plug-ins/`
- **Windows**: `%APPDATA%\GIMP\3.0\plug-ins\`
- **macOS**: `~/Library/Application Support/GIMP/3.0/plug-ins/`

---

## 2. The Modern Python Plugin Template

The following template uses the **ProcedureConfig** pattern, which is the most stable and recommended approach for GIMP 3.0.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk

class MyPlugin(Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        # Return unique internal PDB name(s)
        return ["python-fu-my-plugin"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run,  # The callback function
            None
        )
        
        procedure.set_menu_label("My Cool Plugin")
        procedure.add_menu_path("<Image>/Filters/MyCategory/")
        procedure.set_documentation("Short blurb", "Detailed help", name)
        procedure.set_attribution("Author Name", "Copyright", "2026")
        
        # Image types plugin works on (* for all, RGB, GRAY, etc.)
        procedure.set_image_types("*")
        
        # Sensitivity: when is the menu item enabled?
        procedure.set_sensitivity_mask(Gimp.ProcedureSensitivityMask.DRAWABLE)
        
        # Define arguments (Creates properties in GimpProcedureConfig)
        procedure.add_int_argument(
            "my-integer",
            "Integer Label",
            "Description of this param",
            1, 1000, 100,  # Min, Max, Default
            GObject.ParamFlags.READWRITE
        )
        
        return procedure

    # Standard GIMP 3.0 run signature for ImageProcedure
    def run(self, procedure, run_mode, image, drawables, config, data):
        # 1. Parameter Access (ProcedureConfig pattern)
        my_int = config.get_property("my-integer")

        # 2. Interactive Mode Handling
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("my-plugin-id")
            dialog = GimpUi.ProcedureDialog.new(procedure, config, "My Plugin")
            dialog.fill(None)  # Auto-generate UI for all properties
            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
            
            # Values in 'config' are automatically updated after dialog.run()
            my_int = config.get_property("my-integer")

        # 3. Core Processing
        image.undo_group_start()
        try:
            # logic here...
            Gimp.message(f"Running with value: {my_int}")
        except Exception as e:
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error(str(e)))
        finally:
            image.undo_group_end()
            Gimp.displays_flush()
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

if __name__ == "__main__":
    Gimp.main(MyPlugin.__gtype__, sys.argv)
```

---

## 3. Core API Reference (GIMP 3.0)

### Argument Types
| Method | UI Element |
|--------|------------|
| `add_int_argument` | Spin button |
| `add_double_argument` | Spin button |
| `add_boolean_argument` | Checkbox |
| `add_string_argument` | Text box |
| `add_choice_argument` | Dropdown |
| `add_color_argument` | Color picker |
| `add_file_argument` | File / Folder picker |

### Common Image/Layer Methods
GIMP 3.0 uses GETTERS. Direct property access (like `.width`) usually fails.

```python
width = image.get_width()
height = image.get_height()
layers = image.get_layers()  # Returns List[Gimp.Layer]
layer = Gimp.Layer.new(image, "Name", w, h, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
image.insert_layer(layer, parent=None, position=0)
```

---

## 4. Drawing & Manipulation

Drawing with brushes (`Gimp.pencil`, `Gimp.paint_brush`) can be fragile if the brush isn't found. A robust alternative is using Selections and Fills.

```python
# Save context
Gimp.context_push()

# Set Color (GEGL based)
from gi.repository import Gegl
color = Gegl.Color.new("red")
Gimp.context_set_foreground(color)

# Draw a 2px vertical line
image.select_rectangle(Gimp.ChannelOps.REPLACE, x, 0, 2, height)
layer.edit_fill(Gimp.FillType.FOREGROUND)

# Cleanup
image.select_none()
Gimp.context_pop()
```

---

## 5. Working with the PDB (Procedure Database)

To call other GIMP functions or plugins:

```python
pdb = Gimp.get_pdb()
procedure = pdb.lookup_procedure("gimp-image-scale")
config = procedure.create_config()
config.set_property("image", image)
config.set_property("new-width", 800)
config.set_property("new-height", 600)
result = procedure.run(config)
```

---

## 6. Debugging Workflow

1. **Clear Cache**: If you change the plugin signature, delete `~/.config/GIMP/3.0/pluginrc` to force GIMP to re-register the plugin.
2. **Terminal Output**: Start GIMP from a terminal to see `print()` statements and crash logs.
3. **Log File**: Use a log file for persistent debugging.
   ```python
   def log(msg):
       with open("/tmp/gimp.log", "a") as f:
           f.write(f"{msg}\n")
   ```
4. **Error Console**: Use `Windows -> Dockable Dialogs -> Error Console`.
5. **Syntax Check**: Run `python3 -m py_compile my-plugin.py` before restarting GIMP.

## 7. Troubleshooting Tips

- **Plugin Missing?** Check names (folder == filename.py), check execution bit (`chmod +x`), check shebang (`#!/usr/bin/env python3`).
- **Signature Errors?** Ensure your `run` method matches the number of objects GIMP passes. Use `run(self, *args)` and log `len(args)` if unsure.
- **Import Errors?** Use absolute imports for internal libraries by adding the plugin directory to `sys.path`.
