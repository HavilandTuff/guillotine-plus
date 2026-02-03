#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Guillotine-Plus calculator module.
"""

import sys
import os

# Add project root and plugin dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "guillotine_plus"))

from gplus_lib.calculator import calculate_tile_regions, calculate_cut_lines
from gplus_lib.validator import validate_parameters


class TestCalculateTileRegions:
    """Tests for calculate_tile_regions function."""
    
    def test_basic_grid_no_dividers(self):
        """10x10 grid with 100px tiles on 1000x1000 image."""
        tiles, meta = calculate_tile_regions(1000, 1000, 100, 100, 0)
        assert meta['total_tiles'] == 100
        assert meta['cols'] == 10
        assert meta['rows'] == 10
        assert len(tiles) == 100
    
    def test_grid_with_dividers(self):
        """9x9 grid with 100px tiles and 10px dividers on 1000x1000 image."""
        # 100 + 10 = 110 per tile+divider, fits 9 times (990) with 10px remaining
        tiles, meta = calculate_tile_regions(1000, 1000, 100, 100, 10)
        assert meta['cols'] == 9
        assert meta['rows'] == 9
        assert meta['total_tiles'] == 81
    
    def test_tile_larger_than_image(self):
        """Tile larger than image returns empty."""
        tiles, meta = calculate_tile_regions(500, 500, 600, 600, 0)
        assert meta['total_tiles'] == 0
        assert tiles == []
    
    def test_single_tile(self):
        """Image exactly matches tile size."""
        tiles, meta = calculate_tile_regions(100, 100, 100, 100, 0)
        assert meta['total_tiles'] == 1
        assert meta['cols'] == 1
        assert meta['rows'] == 1
        assert tiles[0] == (0, 0, 100, 100)
    
    def test_rectangular_image(self):
        """Non-square image (1920x1080) with 256px tiles."""
        tiles, meta = calculate_tile_regions(1920, 1080, 256, 256, 0)
        # 1920 / 256 = 7.5 -> 7 cols
        # 1080 / 256 = 4.2 -> 4 rows
        assert meta['cols'] == 7
        assert meta['rows'] == 4
        assert meta['total_tiles'] == 28
    
    def test_tile_positions(self):
        """Verify correct tile positions."""
        tiles, meta = calculate_tile_regions(300, 200, 100, 100, 0)
        expected_positions = [
            (0, 0, 100, 100), (0, 100, 100, 100),
            (100, 0, 100, 100), (100, 100, 100, 100),
            (200, 0, 100, 100), (200, 100, 100, 100),
        ]
        assert tiles == expected_positions


class TestCalculateCutLines:
    """Tests for calculate_cut_lines function."""
    
    def test_cut_lines_no_dividers(self):
        """Cut lines for 3x2 grid."""
        vertical, horizontal = calculate_cut_lines(300, 200, 100, 100, 0)
        assert vertical == [100, 200]
        assert horizontal == [100]
    
    def test_cut_lines_with_dividers(self):
        """Cut lines with 10px dividers."""
        # With dividers, cut lines appear at each tile boundary
        # For 1000x1000 image, 100px tiles, 10px dividers:
        # First tile ends at 100, next starts at 110, ends at 210, etc.
        vertical, horizontal = calculate_cut_lines(1000, 1000, 100, 100, 10)
        # Cuts at: 100, 210, 320, 430, 540, 650, 760, 870, 980
        expected_v = [100, 210, 320, 430, 540, 650, 760, 870, 980]
        expected_h = [100, 210, 320, 430, 540, 650, 760, 870, 980]
        assert vertical == expected_v, f"Got {vertical}"
        assert horizontal == expected_h, f"Got {horizontal}"


class TestValidateParameters:
    """Tests for validate_parameters function."""
    
    def test_valid_parameters(self):
        """Valid parameters should return True."""
        is_valid, error = validate_parameters(1000, 1000, 100, 100, 0)
        assert is_valid is True
        assert error is None
    
    def test_tile_width_exceeds_image(self):
        """Tile width larger than image."""
        is_valid, error = validate_parameters(100, 100, 200, 50, 0)
        assert is_valid is False
        assert "Tile width" in error
    
    def test_tile_height_exceeds_image(self):
        """Tile height larger than image."""
        is_valid, error = validate_parameters(100, 100, 50, 200, 0)
        assert is_valid is False
        assert "Tile height" in error
    
    def test_zero_tile_width(self):
        """Zero tile width is invalid."""
        is_valid, error = validate_parameters(100, 100, 0, 50, 0)
        assert is_valid is False
        assert "positive" in error.lower()
    
    def test_negative_divider(self):
        """Negative divider is invalid."""
        is_valid, error = validate_parameters(100, 100, 50, 50, -5)
        assert is_valid is False
        assert "negative" in error.lower()


def run_tests():
    """Run all tests and report results."""
    test_classes = [
        TestCalculateTileRegions,
        TestCalculateCutLines,
        TestValidateParameters,
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    getattr(instance, method_name)()
                    print(f"✓ {test_class.__name__}.{method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"✗ {test_class.__name__}.{method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"✗ {test_class.__name__}.{method_name}: Exception - {e}")
                    failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
