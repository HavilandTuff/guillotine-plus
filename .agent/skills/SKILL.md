---
description: GIMP 3.0 Python plugin development workflow using GObject Introspection API
---

# GIMP 3.0 Plugin Development Workflow

This skill provides a comprehensive workflow for developing GIMP 3.0 plugins using **Python 3** and the **GObject Introspection (GI)** API.

> [!IMPORTANT]
> GIMP 3.0 uses a completely different API than GIMP 2.10. The old `gimpfu` and `pdb` modules are replaced with GObject Introspection bindings.

## Prerequisites

### System Requirements
- GIMP 3.0+ (AppImage, Flatpak, or native installation)
- Python 3.x (bundled with GIMP 3.0)
- GTK 3.0 development libraries

### Verify Installation

```bash
# For AppImage installation (e.g., in ~/.local/bin/)
~/.local/bin/GIMP-*.AppImage --version

# Or if added to PATH
gimp --version

# Should show GIMP 3.0.x
```

---

## 1. Development Environment Setup

### Plugin Directory Locations (GIMP 3.0)

| Operating System | Plugin Path |
|------------------|-------------|
| **Linux** | `~/.config/GIMP/3.0/plug-ins/` |
| **macOS** | `~/Library/Application Support/GIMP/3.0/plug-ins/` |
| **Windows** | `%APPDATA%\GIMP\3.0\plug-ins\` |

### GIMP 3.0 Plugin Structure (REQUIRED)

> [!WARNING]
> GIMP 3.0 requires each plugin to be in its own subdirectory, with the main Python file matching the folder name exactly.

```
~/.config/GIMP/3.0/plug-ins/
├── my-plugin/
│   └── my-plugin.py          # MUST match folder name
├── another-plugin/
│   └── another-plugin.py
└── guillotine-plus/
    └── guillotine-plus.py
```

### Initial Setup Commands

```bash
# Linux - Create plugin directory
mkdir -p ~/.config/GIMP/3.0/plug-ins/your-plugin-name

# Create symbolic link for development
ln -s /path/to/your-project/your-plugin-name ~/.config/GIMP/3.0/plug-ins/your-plugin-name
```

---

## 2. Plugin Templates

### Minimal Plugin Template (GIMP 3.0)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk

class MyPlugin(Gimp.PlugIn):
    """My GIMP 3.0 Plugin"""

    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        """Return list of procedure names this plugin provides"""
        return ["my-plugin-procedure"]

    def do_set_i18n(self, name):
        """Internationalization - return False to disable"""
        return False

    def do_create_procedure(self, name):
        """Create and configure the procedure"""
        procedure = Gimp.ImageProcedure.new(
            self,
            name,
            Gimp.PDBProcType.PLUGIN,
            self.run,
            None
        )
        
        # Menu configuration
        procedure.set_menu_label("My Plugin")
        procedure.add_menu_path("<Image>/Filters/MyCategory/")
        
        # Documentation
        procedure.set_documentation(
            "Short description",
            "Detailed help text",
            name
        )
        procedure.set_attribution("Author", "Copyright", "2026")
        
        # Add parameters (creates UI automatically)
        procedure.add_int_argument(
            "tile-width",
            "Tile Width",
            "Width of each tile in pixels",
            1, 10000, 100,  # min, max, default
            GObject.ParamFlags.READWRITE
        )
        
        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, args, run_data):
        """Main plugin execution"""
        
        # Get parameter values
        tile_width = args.index(0)
        
        # Show dialog if interactive mode
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("my-plugin")
            dialog = GimpUi.ProcedureDialog.new(procedure, args, "My Plugin")
            dialog.fill(None)  # Auto-generate UI from parameters
            if not dialog.run():
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, GLib.Error())
        
        # Start undo group
        image.undo_group_start()
        
        try:
            # Your plugin logic here
            Gimp.message(f"Processing with tile width: {tile_width}")
            
        except Exception as e:
            Gimp.message(f"Error: {str(e)}")
            return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
        
        finally:
            image.undo_group_end()
            Gimp.displays_flush()
        
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

Gimp.main(MyPlugin.__gtype__, __file__)
```

### Parameter Types Reference (GIMP 3.0)

| Method | Description | Signature |
|--------|-------------|-----------|
| `add_int_argument()` | Integer input | `(name, nick, blurb, min, max, default, flags)` |
| `add_double_argument()` | Float input | `(name, nick, blurb, min, max, default, flags)` |
| `add_string_argument()` | Text input | `(name, nick, blurb, default, flags)` |
| `add_boolean_argument()` | Checkbox | `(name, nick, blurb, default, flags)` |
| `add_color_argument()` | Color picker | `(name, nick, blurb, has_alpha, default, flags)` |
| `add_file_argument()` | File picker | `(name, nick, blurb, flags)` |
| `add_choice_argument()` | Dropdown | `(name, nick, blurb, choice, default, flags)` |

---

## 3. Common API Patterns (GIMP 3.0)

### Image Operations

```python
# Get image dimensions (use getter methods, not properties!)
width = image.get_width()
height = image.get_height()

# Get active layer
layer = image.get_active_layer()

# Get all layers
layers = image.get_layers()

# Duplicate image
new_image = image.duplicate()

# Display new image
Gimp.Display.new(new_image)

# Crop image
image.crop(new_width, new_height, offset_x, offset_y)
```

### Layer Operations

```python
# Create new layer
layer = Gimp.Layer.new(
    image,                    # Parent image
    "Layer Name",             # Name
    width,                    # Width
    height,                   # Height
    Gimp.ImageType.RGBA_IMAGE,  # Type
    100.0,                    # Opacity (0-100)
    Gimp.LayerMode.NORMAL     # Blend mode
)

# Add layer to image
image.insert_layer(layer, None, 0)  # parent, position

# Remove layer
image.remove_layer(layer)

# Duplicate layer
new_layer = layer.copy()
image.insert_layer(new_layer, None, 0)
```

### Selection Operations

```python
# Select rectangle
image.select_rectangle(
    Gimp.ChannelOps.REPLACE,  # Operation
    x, y,                      # Position
    width, height              # Size
)

# Select all
Gimp.Selection.all(image)

# Select none
Gimp.Selection.none(image)

# Invert selection
Gimp.Selection.invert(image)
```

### File Operations

```python
# Get PDB for file operations
pdb = Gimp.get_pdb()

# Export as PNG
file = Gio.File.new_for_path("/path/to/output.png")
pdb.run_procedure("file-png-export", [
    GObject.Value(Gimp.RunMode, Gimp.RunMode.NONINTERACTIVE),
    GObject.Value(Gimp.Image, image),
    GObject.Value(GObject.TYPE_INT, 1),  # num drawables
    GObject.Value(Gimp.ObjectArray, [layer]),  # drawables
    GObject.Value(Gio.File, file),
])
```

### Progress and Messaging

```python
# Show message to user
Gimp.message("Operation complete!")

# Initialize progress bar
Gimp.progress_init("Processing...")

# Update progress (0.0 to 1.0)
Gimp.progress_update(0.5)

# Set progress text
Gimp.progress_set_text("Step 2 of 5...")

# End progress
Gimp.progress_end()
```

---

## 4. Key Differences from GIMP 2.10

| GIMP 2.10 (Python-Fu) | GIMP 3.0 (GI API) |
|-----------------------|-------------------|
| `from gimpfu import *` | `from gi.repository import Gimp, GimpUi` |
| `gimp.pdb.function()` | `Gimp.get_pdb().lookup_procedure()` |
| `image.width` | `image.get_width()` |
| `image.active_layer` | `image.get_active_layer()` |
| `pdb.gimp_message()` | `Gimp.message()` |
| `gimpfu.register()` | Class inheriting `Gimp.PlugIn` |
| Single plugin file | Plugin in named subdirectory |

---

## 5. Testing Workflow

### Quick Test Cycle

1. **Edit plugin code** in your project directory
2. **Restart GIMP** (plugins are loaded at startup)
3. **Test via menu** path defined in `add_menu_path()`
4. **Check error console**: `Windows → Dockable Dialogs → Error Console`

### Debug Output

```python
# Print to terminal (when GIMP started from terminal)
print(f"Debug: variable = {variable}")

# Show in GIMP (visible to user)
Gimp.message(f"Debug: {variable}")

# Write to log file
with open("/tmp/gimp_plugin_debug.log", "a") as f:
    f.write(f"Debug: {variable}\n")
```

### Running GIMP from Terminal (for debug output)

```bash
# For AppImage
~/.local/bin/GIMP-*.AppImage 2>&1 | tee /tmp/gimp_output.log

# Standard installation
gimp --verbose 2>&1 | tee /tmp/gimp_output.log
```

---

## 6. Troubleshooting

### Plugin Not Appearing in Menu

1. **Check folder structure**: Plugin must be in `pluginname/pluginname.py`
2. **Check file is executable**: `chmod +x plugin.py`
3. **Verify shebang line**: `#!/usr/bin/env python3`
4. **Check for syntax errors**: `python3 -m py_compile plugin.py`
5. **Check GIMP error console** for registration errors
6. **Verify GI imports**: Ensure `gi.require_version()` calls are correct

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `gi.repository not found` | GI not installed | Install `python3-gi` package |
| `Gimp.PlugIn` not subclassed | Wrong class structure | Inherit from `Gimp.PlugIn` |
| `AttributeError: 'Image' has no attribute 'width'` | Using old property syntax | Use `image.get_width()` |
| Plugin grayed out | Wrong image type | Check menu path and image requirements |

---

## 7. Project Workflow Checklist

- [ ] Create project directory with version control
- [ ] Create plugin subdirectory matching plugin name
- [ ] Set up symbolic link to GIMP 3.0 plugins folder
- [ ] Create minimal plugin template
- [ ] Verify plugin loads in GIMP 3.0
- [ ] Implement core functionality using GI API
- [ ] Add progress feedback for long operations
- [ ] Implement error handling with proper return values
- [ ] Test edge cases
- [ ] Write README with installation instructions
- [ ] Package for distribution

---

## Resources

- [GIMP 3.0 Python Plugin Tutorial](https://www.gimp.org/docs/)
- [GIMP C-API Documentation](https://developer.gimp.org/api/3.0/) (Python mirrors this)
- [GObject Introspection Docs](https://gi.readthedocs.io/)
- GIMP Procedure Browser: `Help → Procedure Browser` in GIMP
