# Guillotine-Plus Phase 2: Core Functionality - UI & Logic

> **Duration:** 3-5 Days  
> **Goal:** Implement calculation logic for cut positions and add live preview functionality.  
> **Target Platform:** GIMP 3.0+ with Python 3 and GObject Introspection API

---

## Current State

The plugin skeleton is complete:
- [x] GIMP 3.0 registration working (`guillotine_plus/guillotine_plus.py`)
- [x] Auto-generated dialog with Tile Width, Tile Height, Divider Width parameters
- [x] Menu entry at `Filters -> Utils -> Guillotine-Plus`

---

## 1. Calculation Logic Module

### 1.1 Create `lib/calculator.py`

Implement pure Python functions (testable outside GIMP):

```python
def calculate_tile_regions(image_width, image_height, tile_width, tile_height, divider_width):
    """
    Calculate tile regions for slicing.
    
    Returns:
        List of tuples: [(x, y, width, height), ...]
    """
```

**Algorithm:**
```
current_x = 0
while current_x + tile_width <= image_width:
    current_y = 0
    while current_y + tile_height <= image_height:
        tiles.append((current_x, current_y, tile_width, tile_height))
        current_y += tile_height + divider_width
    current_x += tile_width + divider_width
```

**Tasks:**
- [ ] Create `lib/__init__.py`
- [ ] Create `lib/calculator.py` with `calculate_tile_regions()` function
- [ ] Handle edge case: tile size > image size (return empty list)
- [ ] Handle edge case: divider_width = 0 (contiguous tiles)
- [ ] Return metadata: `{"rows": int, "cols": int, "total_tiles": int}`

---

### 1.2 Create `lib/validator.py`

Input validation before calculations:

```python
def validate_parameters(image_width, image_height, tile_width, tile_height, divider_width):
    """
    Validate user input parameters.
    
    Returns:
        (is_valid: bool, error_message: str or None)
    """
```

**Validation Rules:**
| Rule | Error Message |
|------|---------------|
| tile_width > image_width | "Tile width exceeds image width" |
| tile_height > image_height | "Tile height exceeds image height" |
| tile_width + divider_width > image_width | "No tiles can be created with these settings" |
| tile_width <= 0 or tile_height <= 0 | "Tile dimensions must be positive" |

**Tasks:**
- [ ] Create `lib/validator.py` with `validate_parameters()` function
- [ ] Return tuple `(is_valid, error_message)`

---

## 2. Preview Layer Implementation

### 2.1 Create `lib/preview.py`

Manage temporary preview layer in GIMP:

```python
def create_preview_layer(image, name="Guillotine-Plus Preview"):
    """Create a transparent layer for preview lines."""
    
def draw_cut_lines(image, layer, tile_regions, line_color=(255, 0, 0, 128)):
    """Draw red semi-transparent lines showing where cuts will occur."""
    
def remove_preview_layer(image, layer):
    """Remove the preview layer from the image."""
```

**GIMP 3.0 API for Drawing:**
```python
# Create RGBA layer
layer = Gimp.Layer.new(
    image, "Guillotine-Plus Preview",
    image.get_width(), image.get_height(),
    Gimp.ImageType.RGBA_IMAGE, 50.0, Gimp.LayerMode.NORMAL
)
image.insert_layer(layer, None, 0)

# Draw using GeglBuffer or procedural drawing
# Option 1: Use gimp-pencil via PDB
# Option 2: Direct pixel manipulation via GeglBuffer
```

**Tasks:**
- [ ] Create `lib/preview.py`
- [ ] Implement `create_preview_layer()` using GIMP 3.0 GI API
- [ ] Implement `draw_cut_lines()` to visualize tile boundaries
- [ ] Implement `remove_preview_layer()` for cleanup
- [ ] Test that preview layer appears above image content

---

## 3. Integration with Main Plugin

### 3.1 Update `guillotine_plus.py`

Modify the `run()` method to:

1. **Validate parameters** before showing dialog
2. **Calculate tile regions** using `lib/calculator.py`
3. **Show preview** (optional toggle in UI)
4. **Display tile count** in GIMP message

**Updated Run Flow:**
```python
def run(self, procedure, run_mode, image, n_drawables, drawables, args, run_data):
    # 1. Extract parameters
    tile_width = args.index(0)
    tile_height = args.index(1)
    divider_width = args.index(2)
    
    # 2. Show dialog (already implemented)
    
    # 3. Validate parameters
    is_valid, error = validate_parameters(
        image.get_width(), image.get_height(),
        tile_width, tile_height, divider_width
    )
    if not is_valid:
        Gimp.message(f"Error: {error}")
        return procedure.new_return_values(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
    
    # 4. Calculate tiles
    tiles, metadata = calculate_tile_regions(...)
    
    # 5. Create preview layer (Phase 2)
    preview_layer = create_preview_layer(image)
    draw_cut_lines(image, preview_layer, tiles)
    
    # 6. Report results
    Gimp.message(f"Found {metadata['total_tiles']} tiles ({metadata['cols']}x{metadata['rows']})")
```

**Tasks:**
- [ ] Import `lib.calculator` and `lib.validator` in main plugin
- [ ] Call validation before processing
- [ ] Call calculation and show results
- [ ] Create and draw preview layer
- [ ] Clean up preview layer on dialog close/cancel

---

### 3.2 Fix Duplicate Imports

The current `guillotine_plus.py` has duplicate imports (lines 4-10 and 12-18). Clean this up.

**Tasks:**
- [ ] Remove duplicate `import gi` and related imports

---

## 4. Verification Plan

### 4.1 Unit Tests for Calculator

Create `tests/test_calculator.py`:

```bash
cd /home/karol/Dokumenty/PythonProjects/guillotine-plus
python3 -m pytest tests/test_calculator.py -v
```

**Test Cases:**
| Test | Input | Expected Output |
|------|-------|-----------------|
| Basic grid | 1000x1000, tile=100, div=0 | 100 tiles (10x10) |
| With dividers | 1000x1000, tile=100, div=10 | 81 tiles (9x9) |
| Tile > image | 500x500, tile=600, div=0 | 0 tiles |
| Single tile | 100x100, tile=100, div=0 | 1 tile |

### 4.2 Manual Testing in GIMP

1. Open GIMP 3.0 with an image (e.g., 1920x1080)
2. Run `Filters -> Utils -> Guillotine-Plus`
3. Set Tile Width = 256, Tile Height = 256, Divider = 0
4. Click OK
5. **Expected**: Message shows tile count (7x4 = 28 tiles for 1920x1080)
6. **Expected**: Semi-transparent red preview lines appear on image

---

## Phase 2 Checklist Summary

- [ ] Create `lib/__init__.py`
- [ ] Create `lib/calculator.py` with tile region calculation
- [ ] Create `lib/validator.py` with parameter validation
- [ ] Create `lib/preview.py` with preview layer functions
- [ ] Fix duplicate imports in `guillotine_plus.py`
- [ ] Integrate calculator into main plugin
- [ ] Integrate validator into main plugin
- [ ] Integrate preview layer into main plugin
- [ ] Create `tests/test_calculator.py` with unit tests
- [ ] Run unit tests and verify passing
- [ ] Manual test in GIMP 3.0

---

> **Next Phase:** [Phase 3: Slicing Execution](./phase3_slicing.md)
