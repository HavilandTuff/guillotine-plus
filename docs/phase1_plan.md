# Guillotine-Plus Phase 1: Planning and Setup

> **Duration:** 1-2 Days  
> **Goal:** Understand requirements, set up development environment, and outline core architecture.  
> **Target Platform:** GIMP 3.0+ with Python 3 and GObject Introspection API

---

## 1. Detailed Requirements Gathering & Edge Cases

> [!IMPORTANT]
> This plugin targets **GIMP 3.0** which uses **Python 3** and the new **GObject Introspection (GI)** API. This is a breaking change from GIMP 2.10's Python-Fu.

### 1.1 Define Edge Case Behaviors

| Edge Case | Expected Behavior | Priority |
|-----------|-------------------|----------|
| Tile size + divider > image size | Disable "Cut" button, show warning message | High |
| Image smaller than single tile | Warn user, disable cutting | High |
| Non-divisible dimensions | Discard excess pixels at right/bottom, inform user | Medium |
| Zero divider width | Treat as no dividers (contiguous tiles) | Medium |
| Very large images (>10000px) | Implement progress feedback | Medium |

### 1.2 Feature Scope Definition

- [ ] **Active Layer Only:** Initial version works on active layer only
- [ ] **Undo Support:** Rely on GIMP's built-in undo functionality
- [ ] **Multi-layer:** Document as future enhancement (Phase 5+)

### 1.3 Document Decisions

- [ ] Create `DECISIONS.md` file to track architectural decisions
- [ ] Document rationale for each edge case handling approach

---

## 2. GIMP 3.0 Plugin Development Environment Setup

### 2.1 Verify GIMP 3.0 Installation

GIMP 3.0 is installed as an **AppImage** in `~/.local/bin/`:

```bash
# Check GIMP 3.0 AppImage location
ls -la ~/.local/bin/GIMP*

# Verify version (adjust filename as needed)
~/.local/bin/GIMP-*.AppImage --version

# Or if added to PATH
gimp --version
```

- [ ] Confirm GIMP 3.0 AppImage is executable
- [ ] Verify Python 3 support is enabled

### 2.2 Plugin Directory for GIMP 3.0

> [!WARNING]
> GIMP 3.0 requires a **new directory structure**: each plugin must be in its own subdirectory, with the main file sharing the same name as the folder.

| OS | Plugin Path |
|----|-------------|
| Linux | `~/.config/GIMP/3.0/plug-ins/` |
| macOS | `~/Library/Application Support/GIMP/3.0/plug-ins/` |
| Windows | `%APPDATA%\GIMP\3.0\plug-ins\` |

**GIMP 3.0 Structure:**
```
~/.config/GIMP/3.0/plug-ins/
└── guillotine-plus/
    └── guillotine-plus.py    # Main file MUST match folder name
```

- [ ] Create plugin directory: `mkdir -p ~/.config/GIMP/3.0/plug-ins/guillotine-plus`
- [ ] Verify directory has write permissions

### 2.3 Create Hello World Test Plugin (GIMP 3.0 / GI API)

Create file: `~/.config/GIMP/3.0/plug-ins/hello-world/hello-world.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk

class HelloWorld(Gimp.PlugIn):
    """Hello World test plugin for GIMP 3.0"""

    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return ["hello-world-python"]

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
        procedure.set_menu_label("Hello World (Python 3)")
        procedure.add_menu_path("<Image>/Filters/Test/")
        procedure.set_documentation(
            "Hello World Test",
            "Test plugin to verify GIMP 3.0 Python setup",
            name
        )
        procedure.set_attribution("Your Name", "Your Name", "2026")
        return procedure

    def run(self, procedure, run_mode, image, n_drawables, drawables, args, run_data):
        Gimp.message("Hello from Guillotine-Plus! GIMP 3.0 + Python 3 works!")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

Gimp.main(HelloWorld.__gtype__, __file__)
```

- [ ] Create plugin directory: `mkdir -p ~/.config/GIMP/3.0/plug-ins/hello-world`
- [ ] Create the test plugin file
- [ ] Make executable: `chmod +x ~/.config/GIMP/3.0/plug-ins/hello-world/hello-world.py`
- [ ] Restart GIMP
- [ ] Verify plugin appears in Filters → Test → Hello World (Python 3)
- [ ] Run plugin and confirm message appears

---

## 3. Basic Architecture Design (GIMP 3.0)

### 3.1 Component Structure

```
guillotine-plus/
├── guillotine-plus/              # Plugin subfolder (matches plugin name)
│   └── guillotine-plus.py        # Main plugin file (matches folder name)
├── lib/
│   ├── __init__.py
│   ├── calculator.py             # Cut position calculations
│   ├── preview.py                # Preview layer management
│   └── slicer.py                 # Image slicing operations
├── tests/
│   └── test_calculator.py        # Unit tests for calculation logic
├── README.md
├── DECISIONS.md
└── LICENSE
```

### 3.2 UI Component Design (GIMP 3.0 GimpProcedureDialog)

GIMP 3.0 uses `GimpProcedureDialog` for automatic UI generation:

- [ ] Define procedure arguments (UI fields auto-generated):
  - `Gimp.Int` for Tile Width (min: 1, max: 10000)
  - `Gimp.Int` for Tile Height (min: 1, max: 10000)
  - `Gimp.Int` for Divider Width (min: 0, max: 1000)
  - `GObject.ParamString` for Output Directory
  - `GObject.ParamString` for Filename Prefix

### 3.3 Logic Component Design

- [ ] Define `calculate_horizontal_cuts(image_width, tile_width, divider_width)` function signature
- [ ] Define `calculate_vertical_cuts(image_height, tile_height, divider_height)` function signature
- [ ] Return format: List of tuples `[(start_x, end_x), ...]`

### 3.4 GIMP 3.0 API Integration Points

| Operation | GIMP 3.0 API |
|-----------|--------------|
| Get image dimensions | `image.get_width()` / `image.get_height()` |
| Create layer | `Gimp.Layer.new(image, name, width, height, type, opacity, mode)` |
| Add layer to image | `image.insert_layer(layer, parent, position)` |
| Remove layer | `image.remove_layer(layer)` |
| Show messages | `Gimp.message(text)` |
| Progress updates | `Gimp.progress_init()` / `Gimp.progress_update()` |
| Get PDB procedure | `Gimp.get_pdb().lookup_procedure(name)` |

### 3.5 Key GIMP 3.0 Import Pattern

```python
import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gimp, GimpUi, GObject, GLib, Gtk
```

---

## 4. Version Control Setup

### 4.1 Initialize Repository

```bash
cd /home/karol/Dokumenty/PythonProjects/guillotine-plus
git init
```

### 4.2 Create .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
*.egg
.venv/
venv/

# GIMP temporary files
*~
*.xcf~
*.bak

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Test outputs
test_output/
```

### 4.3 Create Initial Files

- [ ] Initialize git repository
- [ ] Create `.gitignore`
- [ ] Create `README.md` with project overview (mentioning GIMP 3.0 + Python 3)
- [ ] Create `LICENSE` (choose MIT or GPL to match GIMP)
- [ ] Create initial directory structure
- [ ] Make initial commit

---

## 5. Acceptance Criteria for Phase 1 Completion

| Criterion | Verification |
|-----------|--------------|
| Edge cases documented | `DECISIONS.md` exists with all edge case decisions |
| Dev environment ready | Hello World plugin runs successfully in GIMP 3.0 |
| Architecture documented | Directory structure created with GIMP 3.0 patterns |
| Version control active | Git initialized with initial commit |
| GIMP 3.0 API understood | Team familiar with GObject Introspection imports |

---

## Phase 1 Checklist Summary

- [ ] Requirements & edge cases documented in `DECISIONS.md`
- [x] GIMP 3.0 AppImage verified working (`~/.local/bin/`)
- [x] Plugin directory created with correct GIMP 3.0 structure
- [x] Hello World test plugin created and tested (Python 3 + GI API)
- [x] Architecture design documented for GIMP 3.0
- [x] Git repository initialized with proper `.gitignore`
- [x] `README.md` with project overview created
- [x] Initial directory structure created
- [x] First commit made

---

> **Next Phase:** [Phase 2: Core Functionality - UI & Logic](./phase2_ui_logic.md)
