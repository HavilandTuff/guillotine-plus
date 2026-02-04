# Guillotine-Plus

A powerful GIMP 3.0 plugin designed to efficiently slice images into tiles. Whether you need a perfectly even grid or specific custom cuts, Guillotine-Plus offers a modern, visual approach to image slicing.

## Features

- **Two Slicing Methods**:
    - **Fixed Grid**: Slice into even tiles based on specific width and height.
    - **Use Guides**: Slice the image based on existing horizontal and vertical GIMP guides.
- **Divider Support**: Define discardable divider widths (gutters) between grid tiles.
- **Minimum Size Filter**: (Guide Mode) Automatically skip tiny scraps or accidental slivers by setting a minimum dimension limit.
- **Live Preview**: Visualize exactly where cuts will happen before executing.
- **Batch Export**: Automatically save all slices as separate files.
    - Supported formats: **PNG, JPEG, WebP**.
    - Customizable metadata preservation and filename prefixes.
- **Non-Destructive**: Operates on a duplicate of your image to keep your original project safe.

## Target Platform

- **GIMP 3.0+** (utilizing the modern GObject Introspection API)
- **Python 3**

## Installation

1. Ensure GIMP 3.0 is installed.
2. Link or copy the `guillotine_plus` directory to your GIMP 3.0 plugins folder:
   - **Linux**: `~/.config/GIMP/3.0/plug-ins/`
3. Restart GIMP.
4. Find the plugin under `Filters -> Utils -> Guillotine-Plus`.

## 🤖 LLM-Assisted Development & Warning

This plugin was developed with significant assistance from **Large Language Models (LLMs)**. While this allowed for rapid implementation of modern GIMP 3.0 API features, please be aware of the following:

> [!WARNING]
> **Use at your own risk.** 
> Although the slicing algorithm is designed to be non-destructive (working on duplicates), software generated with AI assistance may contain edge-case bugs or unconventional API usages that could lead to GIMP crashes or unexpected behavior. Always save your work before running automated slicing on large projects.

## Development

The project is structured for modularity:
- `guillotine_plus/guillotine_plus.py`: Main entry point and GIMP procedure registration.
- `guillotine_plus/gplus_lib/`:
    - `calculator.py`: Grid mathematics.
    - `guide_manager.py`: Guide retrieval and region logic.
    - `slicer.py`: Image manipulation and file export.
    - `preview.py`: Canvas visualization.
    - `validator.py`: Parameter safety checks.
