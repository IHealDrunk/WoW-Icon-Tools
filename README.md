# WoW Icon Tools

Automated World of Warcraft icon processing pipeline.

## Overview

WoW Icon Tools converts extracted World of Warcraft icon assets into custom styled TGA icons using configurable GIMP templates.

The project is designed to create complete icon collections while allowing multiple visual designs.

## Features

- BLP to PNG conversion
- Automatic icon filtering
- 128x128 resizing
- Icon cropping and enhancement
- GIMP template processing
- TGA export
- Resume processing after interruption
- Batch statistics and error reporting

## Workflow
BLP Files
|
v
PNG Conversion
|
v
128x128 Processing
|
v
GIMP Template Processing
|
v
Final TGA Icons

## Icon Collections

### Eclipse Icons

Premium style:

- Border
- Shadow
- Glow
- Gloss/Glare effects

### Obsidian Icons

Minimal style:

- Border
- Shadow
- No gloss
- Clean appearance

## Requirements

- Python 3.x
- Pillow
- GIMP 3.x
- GIMP Python support

## Project Structure
WoW Icon Tools

Scripts/
blp_to_png.py
icon_resize_128.py
wow_icon_tools.py

Templates/

Documentation/

Logs/

## Version History

### v1.0.3

- Added resume processing
- Added export checking
- Added processing statistics
- Successfully tested with 31,995 icons
