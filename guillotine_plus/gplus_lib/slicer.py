#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2024 Karol
# Licensed under the GNU General Public License v3.0
#
"""
Image slicing and export functionality for Guillotine-Plus.
"""

from typing import List, Tuple, Optional, Callable
import os

try:
    import gi
    gi.require_version('Gimp', '3.0')
    from gi.repository import Gimp, GObject, Gio, Gegl
    GIMP_AVAILABLE = True
except (ImportError, ValueError):
    GIMP_AVAILABLE = False


def slice_image(
    image,
    tiles: List[Tuple[int, int, int, int]],
    output_dir_file: Gio.File,
    prefix: str,
    format_ext: str,
    log_func: Optional[Callable[[str], None]] = None
) -> Tuple[int, List[str]]:
    """
    Slice an image into tiles and save each to disk.
    
    Args:
        image: GIMP image object
        tiles: List of (x, y, width, height) tuples
        output_dir_file: Gio.File representing the output directory
        prefix: Filename prefix
        format_ext: Output format (png, jpg, webp)
        log_func: Optional logging function
    
    Returns:
        Tuple of (success_count, list_of_saved_paths)
    """
    if not GIMP_AVAILABLE:
        if log_func: log_func("GIMP not available in slicer")
        return 0, []

    output_path = output_dir_file.get_path()
    if not output_path or not os.path.exists(output_path):
        if log_func: log_func(f"Output directory does not exist: {output_path}")
        return 0, []

    # 1. Prepare image: Merge visible layers as requested by user
    # We work on a duplicate to avoid destructive changes to original
    temp_image = image.duplicate()
    try:
        # Flatten visible layers
        # In GIMP 3.0, we can use item_merge_visible_layers or flatten
        # Since user asked to "flatten/merge visible layers first", flatten is easiest if they want one result per tile.
        # However, if there are transparent areas they want to keep, merge_visible might be better. 
        # "Flatten" usually means adding a background.
        # Let's use merge_visible_layers.
        merged_layer = temp_image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
        
        saved_paths = []
        total = len(tiles)
        
        Gimp.progress_init(f"Slicing into {total} tiles...")
        
        for idx, (x, y, w, h) in enumerate(tiles):
            Gimp.progress_set_text(f"Processing tile {idx + 1}/{total}")
            Gimp.progress_update(idx / total)
            
            # Select the region
            temp_image.select_rectangle(Gimp.ChannelOps.REPLACE, x, y, w, h)
            
            # Copy and paste as new image
            if Gimp.edit_copy([merged_layer]):
                # In GIMP 3.0, edit_paste_as_new_image is often available via PDB 
                # or as a wrapper. Let's try the wrapper first, but with a fallback.
                tile_image = None
                try:
                    tile_image = Gimp.edit_paste_as_new_image()
                except:
                    # Fallback to PDB
                    try:
                        pdb = Gimp.get_pdb()
                        # Modern GIMP 3.0 run_procedure returns a result object 
                        # that can be indexed or has a get_values() method
                        result = pdb.run_procedure('gimp-edit-paste-as-new-image', [])
                        # result[0] is status, result[1] is the image
                        if result and len(result) > 1:
                            tile_image = result[1]
                    except:
                        if log_func: log_func("Both wrapper and PDB fallback failed for paste_as_new")
                        continue

                if tile_image:
                    # Generate filename
                    filename = f"{prefix}_{idx + 1:03d}.{format_ext}"
                    full_path = os.path.join(output_path, filename)
                    save_file = Gio.File.new_for_path(full_path)
                    
                    # Try to copy metadata if possible
                    try:
                        metadata = temp_image.get_metadata()
                        if metadata:
                            tile_image.set_metadata(metadata)
                    except:
                        pass
                    
                    # Save the image
                    # Gimp.file_save uses default export options
                    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, tile_image, save_file)
                    
                    saved_paths.append(full_path)
                    tile_image.delete() 
            
        Gimp.progress_update(1.0)
        Gimp.progress_end()
        return len(saved_paths), saved_paths
        
    finally:
        temp_image.delete()
        temp_image = None


def check_for_overwrites(output_dir_file: Gio.File, prefix: str, count: int, format_ext: str) -> List[str]:
    """Check if any of the target files already exist."""
    existing = []
    output_path = output_dir_file.get_path()
    if not output_path:
        return []
        
    for i in range(1, count + 1):
        filename = f"{prefix}_{i:03d}.{format_ext}"
        full_path = os.path.join(output_path, filename)
        if os.path.exists(full_path):
            existing.append(filename)
    return existing
