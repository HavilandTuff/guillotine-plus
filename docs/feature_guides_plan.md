# Phase 4: Guide-Based Slicing Implementation Plan

## Goal
Enhance **Guillotine-Plus** to detect existing image guides and offer the user a choice:
1.  **Grid Mode**: Construct tiles based on fixed width/height (Current implementation).
2.  **Guide Mode**: Construct tiles based on existing guides (horizontal and vertical).

If Guide Mode is selected, users can optionally set a **Minimum Dimension Limit** to avoid saving tiny scraps or cut-offs.

## User Experience Flow

1.  **Plugin Start**:
    *   Plugin checks if the image has any guides.
    *   **If Guides Exist**:
        *   A new parameter/toggle in the UI becomes available or is prompted: "Method: [Grid / Guides]".
        *   If "Guides" is selected, "Tile Width" and "Tile Height" inputs become disabled or irrelevant.
        *   A new input "Minimum Size (px)" appears (default: 0 or reasonable small value).
    *   **If No Guides**:
        *   Plugin behaves as before (Grid mode only).

2.  **Execution (Guide Mode)**:
    *   Plugin retrieves all guide positions.
    *   Sorts horizontal and vertical guides.
    *   Calculates rectangular regions formed by the grid of these guides.
    *   Filters out regions smaller than "Minimum Size".
    *   Slices and exports these regions using the existing `slicer` module logic.

## Technical Implementation

### 1. New Logic Module: `gplus_lib/guide_manager.py`

Functions needed:
*   `get_image_guides(image) -> (v_guides, h_guides)`
    *   Uses `image.find_next_guide(id)` loop to retrieve all guides.
    *   Checks orientation (`image.get_guide_orientation(id)`).
    *   Returns sorted lists of coordinates.

*   `calculate_guide_regions(width, height, v_guides, h_guides, min_size=0) -> tiles`
    *   Constructs a grid from `[0] + v_guides + [width]` and `[0] + h_guides + [height]`.
    *   Iterates rows and cols to form rectangles.
    *   Checks `w >= min_size` and `h >= min_size`.

### 2. UI Updates (`guillotine_plus.py`)

*   **New Argument**: `slicing-method` (Choice: GRID, GUIDES).
*   **New Argument**: `min-tile-size` (Int).
*   **Dynamic UI**:
    *   If possible in GimpUi, disable/hide Grid parameters when "Guides" is selected.
    *   If not possible to be dynamic easily, just ignore them in logic.
*   **Initialization**:
    *   In `run()`, check guides count.
    *   If count > 0, default `slicing-method` could be GUIDES (or let user choose).

### 3. Slicer Integration

*   Update `slicer.slice_image` to accept a generic `tiles` list (it already does!).
*   The main `run()` method will branch:
    ```python
    if method == GUIDES:
        v_guides, h_guides = get_image_guides(image)
        tiles, meta = calculate_guide_regions(..., v_guides, h_guides, min_size)
    else:
        tiles, meta = calculate_tile_regions(...)
    ```

## Step-by-Step Plan

1.  **Research & Verify**: Confirm `find_next_guide` API works (Test script created).
2.  **Backend Logic**: Create `gplus_lib/guide_manager.py` with calculation logic.
3.  **UI Integration**: Add new arguments to `guillotine_plus.py`.
4.  **Main Logic**: Wire up the "Method" choice to switch between calculation functions.
5.  **Refinement**: Implement the "Minimum Size" filter to handle scraps.

## Open Questions
*   **Dividers**: Do guides imply dividers? Usually guides are 0-width cuts. We will assume 0-width dividers for Guide Mode unless specified otherwise.
*   **Overlapping**: GIMP guides are infinite lines. They form a grid naturally.

