#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2026 HavilandTuff
# Licensed under the GNU General Public License v3.0
#
"""
Tile region calculation logic for Guillotine-Plus.

This module provides pure Python functions for calculating tile positions,
independent of GIMP API for easy unit testing.
"""

from typing import List, Tuple, Dict


def calculate_tile_regions(
    image_width: int,
    image_height: int,
    tile_width: int,
    tile_height: int,
    divider_width: int = 0
) -> Tuple[List[Tuple[int, int, int, int]], Dict[str, int]]:
    """
    Calculate tile regions for slicing an image.
    
    Args:
        image_width: Width of the source image in pixels
        image_height: Height of the source image in pixels
        tile_width: Width of each tile in pixels
        tile_height: Height of each tile in pixels
        divider_width: Width of divider lines between tiles (discarded during cut)
    
    Returns:
        Tuple containing:
        - List of tile regions as (x, y, width, height) tuples
        - Metadata dict with 'rows', 'cols', 'total_tiles'
    
    Example:
        >>> tiles, meta = calculate_tile_regions(1000, 1000, 100, 100, 0)
        >>> len(tiles)
        100
        >>> meta
        {'rows': 10, 'cols': 10, 'total_tiles': 100}
    """
    tiles = []
    
    # Edge case: tile larger than image
    if tile_width > image_width or tile_height > image_height:
        return [], {'rows': 0, 'cols': 0, 'total_tiles': 0}
    
    # Edge case: invalid dimensions
    if tile_width <= 0 or tile_height <= 0:
        return [], {'rows': 0, 'cols': 0, 'total_tiles': 0}
    
    cols = 0
    rows = 0
    
    current_x = 0
    while current_x + tile_width <= image_width:
        cols += 1
        current_y = 0
        row_count = 0
        
        while current_y + tile_height <= image_height:
            tiles.append((current_x, current_y, tile_width, tile_height))
            current_y += tile_height + divider_width
            row_count += 1
        
        # Track rows from first column
        if rows == 0:
            rows = row_count
        
        current_x += tile_width + divider_width
    
    metadata = {
        'rows': rows,
        'cols': cols,
        'total_tiles': len(tiles)
    }
    
    return tiles, metadata


def calculate_cut_lines(
    image_width: int,
    image_height: int,
    tile_width: int,
    tile_height: int,
    divider_width: int = 0
) -> Tuple[List[int], List[int]]:
    """
    Calculate horizontal and vertical cut line positions.
    
    Args:
        image_width: Width of the source image
        image_height: Height of the source image
        tile_width: Width of each tile
        tile_height: Height of each tile
        divider_width: Width of dividers between tiles
    
    Returns:
        Tuple of (vertical_lines_x, horizontal_lines_y)
    """
    vertical_lines = []
    horizontal_lines = []
    
    # Calculate vertical cut lines (x positions)
    current_x = tile_width
    while current_x < image_width:
        vertical_lines.append(current_x)
        current_x += divider_width + tile_width
    
    # Calculate horizontal cut lines (y positions)
    current_y = tile_height
    while current_y < image_height:
        horizontal_lines.append(current_y)
        current_y += divider_width + tile_height
    
    return vertical_lines, horizontal_lines
