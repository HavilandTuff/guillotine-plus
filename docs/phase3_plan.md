# Phase 3: Slicing Execution Plan

This document outlines the implementation plan for Phase 3 of the Guillotine-Plus GIMP plugin, which focuses on implementing the actual image slicing functionality.

## Goal

Implement the actual image slicing using GIMP's PDB functions, allowing users to export individual tiles as separate image files.

---

## Current State

Phase 2 has been completed with the following capabilities:
- Plugin registers and appears in GIMP menu (`Image -> Filters -> Utils -> Guillotine-Plus`).
- User can input `tile-width`, `tile-height`, and `divider-width` parameters.
- Preview layer displays cut lines on the canvas.
- Core calculation logic exists in `gplus_lib/calculator.py`.

**Current `run()` method behavior:**
- Opens parameter dialog.
- Calculates tile regions and cut lines.
- Creates a preview layer with visual cut lines.
- Does **not** perform actual slicing or file export.

---

## New Features for Phase 3

### 1. UI Enhancements

| Parameter | Type | Description |
|-----------|------|-------------|
| `output-directory` | File Chooser | Directory where sliced tiles will be saved |
| `filename-prefix` | String | Prefix for output filenames (e.g., `tile` → `tile_001.png`) |
| `output-format` | Choice | Output format: PNG, JPEG, WEBP |
| `execute-mode` | Choice | `preview` (current behavior) or `slice` (new functionality) |

### 2. Slicing Logic

Create a new module: `gplus_lib/slicer.py`

```python
def slice_image(
    image,
    tiles: List[Tuple[int, int, int, int]],
    output_dir: str,
    prefix: str,
    format: str,
    progress_callback = None
) -> Tuple[int, List[str]]:
    """
    Slice an image into tiles and save each to disk.
    
    Args:
        image: GIMP image object
        tiles: List of (x, y, width, height) tuples
        output_dir: Directory to save files
        prefix: Filename prefix
        format: Output format (png, jpg, webp)
        progress_callback: Optional callback for progress updates
    
    Returns:
        Tuple of (success_count, list_of_saved_paths)
    """
```

---

## Implementation Steps

### Step 1: Add New UI Parameters

**File:** [guillotine_plus.py](file:///home/karol/Dokumenty/PythonProjects/guillotine-plus/guillotine_plus/guillotine_plus.py)

In `do_create_procedure()`:
```python
# Output directory
procedure.add_file_argument(
    "output-directory",
    "Output Directory",
    "Directory where tiles will be saved",
    Gimp.FileChooserAction.SELECT_FOLDER,
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

# Output format (using choice)
choice = Gimp.Choice.new()
choice.add("png", 0, "PNG", "")
choice.add("jpg", 1, "JPEG", "")
choice.add("webp", 2, "WebP", "")
procedure.add_choice_argument(
    "output-format",
    "Output Format",
    "File format for sliced tiles",
    choice,
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
```

---

### Step 2: Create Slicer Module

**File:** [NEW] `gplus_lib/slicer.py`

```python
#!/usr/bin/env python3
"""
Image slicing and export functionality for Guillotine-Plus.
"""

from typing import List, Tuple, Optional, Callable
import os

try:
    import gi
    gi.require_version('Gimp', '3.0')
    from gi.repository import Gimp, Gio
    GIMP_AVAILABLE = True
except (ImportError, ValueError):
    GIMP_AVAILABLE = False


def slice_image(
    image,
    layer,
    tiles: List[Tuple[int, int, int, int]],
    output_dir: str,
    prefix: str,
    format_ext: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[int, List[str]]:
    """Slice image into tiles and save to disk."""
    if not GIMP_AVAILABLE:
        return 0, []
    
    saved_paths = []
    total = len(tiles)
    
    for idx, (x, y, w, h) in enumerate(tiles):
        if progress_callback:
            progress_callback(idx / total, f"Slicing tile {idx + 1}/{total}")
        
        # Create new image from selection
        # ... implementation details
        
        # Generate filename
        filename = f"{prefix}_{idx + 1:03d}.{format_ext}"
        filepath = os.path.join(output_dir, filename)
        
        # Save and close
        # ... GIMP file export API
        
        saved_paths.append(filepath)
    
    return len(saved_paths), saved_paths
```

---

### Step 3: Update Main Run Logic

**File:** [guillotine_plus.py](file:///home/karol/Dokumenty/PythonProjects/guillotine-plus/guillotine_plus/guillotine_plus.py)

Modify the `run()` method to handle both preview and slice modes:

```python
def run(self, procedure, run_mode, image, drawables, config, data):
    # ... existing parameter extraction ...
    
    execute_mode = config.get_property("execute-mode")
    
    if execute_mode == "preview":
        # Existing preview logic
        self._do_preview(image, tiles, v_lines, h_lines)
    else:
        # New slicing logic
        output_dir = config.get_property("output-directory")
        prefix = config.get_property("filename-prefix")
        format_ext = config.get_property("output-format")
        
        self._do_slice(image, drawables, tiles, output_dir, prefix, format_ext)
```

---

### Step 4: Implement Progress Feedback

Use GIMP's progress API for user feedback during slicing:

```python
Gimp.progress_init("Slicing image...")
Gimp.progress_set_text(f"Processing tile {idx + 1}/{total}")
Gimp.progress_update(idx / total)
```

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `guillotine_plus.py` | MODIFY | Add new parameters and slice mode logic |
| `gplus_lib/slicer.py` | NEW | Core slicing and export functionality |
| `gplus_lib/__init__.py` | MODIFY | Export new `slice_image` function |

---

## Verification Plan

### Unit Tests

Create `tests/test_slicer.py`:
- Test filename generation with various prefixes.
- Test output directory handling (non-existent, permissions).
- Mock GIMP API for isolated testing.

### Manual Testing

1. **Preview Mode**: Verify preview still works correctly.
2. **Slice Mode - Basic**: 
   - Load a 1000x1000 image.
   - Set tile size to 100x100, no dividers.
   - Verify 100 files are created with correct dimensions.
3. **Slice Mode - Dividers**:
   - Add 10px dividers.
   - Verify divider regions are skipped.
4. **Error Handling**:
   - Test with read-only output directory.
   - Test with invalid filename prefix (special characters).
5. **Progress Feedback**:
   - Slice a large image and verify progress bar updates.

---

## Estimated Effort

| Task | Estimate |
|------|----------|
| UI Parameters | 0.5 day |
| Slicer Module | 1-2 days |
| Main Logic Integration | 0.5 day |
| Testing & Bug Fixes | 1 day |
| **Total** | **3-4 days** |

---

## Open Questions

1. **Layer handling**: Should we slice only the active layer, or flatten/merge visible layers first?
    - flatten/merge visible layers first
2. **Existing files**: Overwrite, skip, or number increment for existing files?
    - overwrite but ask user first
3. **Metadata preservation**: Should EXIF/metadata be copied to sliced tiles?
    - yes

> [!NOTE]
> These questions should be discussed with the user before implementation.
