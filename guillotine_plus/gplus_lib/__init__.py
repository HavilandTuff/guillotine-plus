# Guillotine-Plus: GIMP 3.0 image slicing plugin
# Copyright (C) 2026 HavilandTuff
# Licensed under the GNU General Public License v3.0
#
"""Core logic modules for Guillotine-Plus plugin."""

from .calculator import calculate_tile_regions
from .validator import validate_parameters
from .guide_manager import get_image_guides, calculate_guide_regions

__all__ = ['calculate_tile_regions', 'validate_parameters', 'get_image_guides', 'calculate_guide_regions']
