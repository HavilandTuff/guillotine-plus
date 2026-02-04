#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2026 HavilandTuff
# Licensed under the GNU General Public License v3.0
#
"""
Parameter validation for Guillotine-Plus.

This module validates user input before processing.
"""

from typing import Tuple, Optional


def validate_parameters(
    image_width: int,
    image_height: int,
    tile_width: int,
    tile_height: int,
    divider_width: int = 0
) -> Tuple[bool, Optional[str]]:
    """
    Validate user input parameters for tile cutting.
    
    Args:
        image_width: Width of the source image
        image_height: Height of the source image
        tile_width: Requested tile width
        tile_height: Requested tile height
        divider_width: Width of dividers between tiles
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if parameters are valid
        - error_message: None if valid, otherwise descriptive error string
    
    Example:
        >>> validate_parameters(1000, 1000, 100, 100, 0)
        (True, None)
        >>> validate_parameters(100, 100, 200, 200, 0)
        (False, 'Tile width (200) exceeds image width (100)')
    """
    # Check for positive dimensions
    if tile_width <= 0:
        return False, "Tile width must be positive"
    
    if tile_height <= 0:
        return False, "Tile height must be positive"
    
    if divider_width < 0:
        return False, "Divider width cannot be negative"
    
    # Check tile fits in image
    if tile_width > image_width:
        return False, f"Tile width ({tile_width}) exceeds image width ({image_width})"
    
    if tile_height > image_height:
        return False, f"Tile height ({tile_height}) exceeds image height ({image_height})"
    
    # Check at least one tile can be created
    # After first tile, we need at least divider + another tile to matter
    # But single tile is valid
    if tile_width + divider_width > image_width and tile_width < image_width:
        return False, "Tile width plus divider exceeds image width - no complete tiles possible"
    
    if tile_height + divider_width > image_height and tile_height < image_height:
        return False, "Tile height plus divider exceeds image height - no complete tiles possible"
    
    return True, None
