#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2026 HavilandTuff
# Licensed under the GNU General Public License v3.0
#
"""
Preview layer management for Guillotine-Plus.

This module handles creating and drawing on the preview layer
to visualize cut lines before execution.
"""

from typing import List, Tuple, Optional

# These imports are only available when running inside GIMP
try:
    import gi
    gi.require_version('Gimp', '3.0')
    gi.require_version('Gegl', '0.4')
    from gi.repository import Gimp, Gegl, GObject
    GIMP_AVAILABLE = True
except (ImportError, ValueError):
    GIMP_AVAILABLE = False


def create_preview_layer(image, name: str = "Guillotine-Plus Preview"):
    """
    Create a transparent layer for preview visualization.
    
    Args:
        image: GIMP image object
        name: Name for the preview layer
    
    Returns:
        The created layer object, or None if creation failed
    """
    if not GIMP_AVAILABLE:
        return None
    
    try:
        width = image.get_width()
        height = image.get_height()
        
        # Create RGBA layer with 50% opacity
        layer = Gimp.Layer.new(
            image,
            name,
            width,
            height,
            Gimp.ImageType.RGBA_IMAGE,
            50.0,  # Opacity
            Gimp.LayerMode.NORMAL
        )
        
        # Insert at top of layer stack
        image.insert_layer(layer, None, 0)
        
        # Fill with transparency
        Gimp.context_push()
        Gimp.context_set_foreground(Gegl.Color.new("transparent"))
        layer.edit_fill(Gimp.FillType.TRANSPARENT)
        Gimp.context_pop()
        
        return layer
        
    except Exception as e:
        Gimp.message(f"Failed to create preview layer: {str(e)}")
        return None


def draw_cut_lines(
    image,
    layer,
    vertical_lines: List[int],
    horizontal_lines: List[int],
    line_color: Tuple[int, int, int] = (255, 0, 0)
):
    """
    Draw cut lines on the preview layer using selections and fill.
    This method is more robust than pencil in GIMP 3.0.
    """
    if not GIMP_AVAILABLE or layer is None:
        return
    
    try:
        width = image.get_width()
        height = image.get_height()
        
        # Save current selection and context
        Gimp.context_push()
        
        # Set drawing color
        color = Gegl.Color.new("red")
        color.set_rgba(
            line_color[0] / 255.0,
            line_color[1] / 255.0,
            line_color[2] / 255.0,
            1.0  # Full alpha for lines
        )
        Gimp.context_set_foreground(color)
        
        # Draw vertical lines (2px wide)
        for x in vertical_lines:
            if 0 < x < width:
                # Select a narrow vertical strip
                image.select_rectangle(Gimp.ChannelOps.REPLACE, x-1, 0, 2, height)
                # Fill the selection on the preview layer
                layer.edit_fill(Gimp.FillType.FOREGROUND)
        
        # Draw horizontal lines (2px wide)
        for y in horizontal_lines:
            if 0 < y < height:
                # Select a narrow horizontal strip
                image.select_rectangle(Gimp.ChannelOps.REPLACE, 0, y-1, width, 2)
                # Fill the selection on the preview layer
                layer.edit_fill(Gimp.FillType.FOREGROUND)
        
        # Cleanup
        image.select_none()
        Gimp.context_pop()
        
        # Refresh display
        Gimp.displays_flush()
        
    except Exception as e:
        Gimp.message(f"Failed to draw cut lines: {str(e)}")


def remove_preview_layer(image, layer):
    """
    Remove the preview layer from the image.
    
    Args:
        image: GIMP image object
        layer: The preview layer to remove
    """
    if not GIMP_AVAILABLE or layer is None:
        return
    
    try:
        image.remove_layer(layer)
        Gimp.displays_flush()
    except Exception as e:
        Gimp.message(f"Failed to remove preview layer: {str(e)}")


def find_preview_layer(image, name: str = "Guillotine-Plus Preview"):
    """
    Find existing preview layer by name.
    
    Args:
        image: GIMP image object
        name: Name of the preview layer to find
    
    Returns:
        The layer if found, None otherwise
    """
    if not GIMP_AVAILABLE:
        return None
    
    try:
        for layer in image.get_layers():
            if layer.get_name() == name:
                return layer
        return None
    except:
        return None
