#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2024 Karol
# Licensed under the GNU General Public License v3.0
#
"""
Guide management and region calculation for Guillotine-Plus.
"""

from typing import List, Tuple, Dict
import sys

try:
    import gi
    gi.require_version('Gimp', '3.0')
    from gi.repository import Gimp, GObject
    GIMP_AVAILABLE = True
except (ImportError, ValueError):
    GIMP_AVAILABLE = False


def get_image_guides(image) -> Tuple[List[int], List[int]]:
    """
    Retrieve all guide positions from the image, sorted by orientation.
    
    Args:
        image: GIMP image object
    
    Returns:
        Tuple of (vertical_guides, horizontal_guides) lists of pixel offsets.
    """
    if not GIMP_AVAILABLE:
        return [], []
    
    v_guides = []
    h_guides = []
    
    try:
        # PDB Fallbacks for properties not exposed directly in GIMP 3 Python
        pdb = Gimp.get_pdb()
        
        guide = image.find_next_guide(0)
        while guide != 0:
            orientation = -1
            position = -1
            
            # Get Orientation
            try:
                orientation = image.get_guide_orientation(guide)
            except:
                res = pdb.run_procedure('gimp-image-get-guide-orientation', [
                    GObject.Value(Gimp.Image, image), 
                    GObject.Value(GObject.TYPE_UINT, guide)
                ])
                if res and len(res) > 1:
                    orientation = res[1]
            
            # Get Position
            try:
                position = image.get_guide_position(guide)
            except:
                res = pdb.run_procedure('gimp-image-get-guide-position', [
                    GObject.Value(Gimp.Image, image),
                    GObject.Value(GObject.TYPE_UINT, guide)
                ])
                if res and len(res) > 1:
                    position = res[1]
            
            if position >= 0:
                # Gimp.OrientationType.VERTICAL is 0? Let's check Gimp.OrientationType
                # Enum: HORIZONTAL (0), VERTICAL (1), UNKNOWN (2)
                # Actually usually in GIMP: ORIENTATION-HORIZONTAL=0, ORIENTATION-VERTICAL=1
                
                if orientation == Gimp.OrientationType.VERTICAL: 
                    v_guides.append(position)
                elif orientation == Gimp.OrientationType.HORIZONTAL:
                    h_guides.append(position)
                else:
                    # If we can't determine, try to infer or skip?
                    # Fallback check against int values if enum fails matching
                    if orientation == 1:
                        v_guides.append(position)
                    elif orientation == 0:
                        h_guides.append(position)
            
            guide = image.find_next_guide(guide)
            
        v_guides.sort()
        h_guides.sort()
        
    except Exception as e:
        # If something fails, just return what we have
        sys.stderr.write(f"Guide retrieval failed: {e}\n")
    
    return v_guides, h_guides


def calculate_guide_regions(
    image_width: int,
    image_height: int,
    v_guides: List[int],
    h_guides: List[int],
    min_size: int = 0
) -> Tuple[List[Tuple[int, int, int, int]], Dict[str, int]]:
    """
    Calculate rectangular regions grid based on guides.
    
    Args:
        image_width: Image total width
        image_height: Image total height
        v_guides: Sorted list of vertical guide x-positions
        h_guides: Sorted list of horizontal guide y-positions
        min_size: Minimum width/height to include in results
        
    Returns:
        Tuple of (List of (x, y, w, h), Metadata dict)
    """
    tiles = []
    
    # Create full grid lines including image boundaries
    # Use set to remove duplicates (e.g. guide at 0 or at width)
    xs = sorted(list(set([0] + v_guides + [image_width])))
    ys = sorted(list(set([0] + h_guides + [image_height])))
    
    rows = len(ys) - 1
    cols = len(xs) - 1
    
    for i in range(cols):
        x = xs[i]
        w = xs[i+1] - x
        
        if w < min_size or w <= 0:
            continue
            
        for j in range(rows):
            y = ys[j]
            h = ys[j+1] - y
            
            # Skip if tool small
            if h < min_size or h <= 0:
                continue
            
            tiles.append((x, y, w, h))
            
    metadata = {
        'rows': rows,
        'cols': cols,
        'total_tiles': len(tiles),
        'method': 'guides'
    }
    
    return tiles, metadata
