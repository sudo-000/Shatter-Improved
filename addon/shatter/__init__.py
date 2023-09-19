"""
The Shatter Smash Hit Level Editor Addon for Blender
Copyright (C) 2020 - 2023 Knot126, licenced under a modified MIT licence

====================================================

This is the main file of Shatter. It configures imports, loads the main module
and calls the register and ungregister functions.
"""

bl_info = {
	"name": "Shatter",
	"description": "Blender-based tools for editing, saving and loading Smash Hit segments.",
	"author": "Shatter Team",
	"version": (2023, 9, 4),
	"blender": (3, 0, 0),
	"location": "File > Import/Export and 3D View > Tools",
	"warning": "",
	"doc_url": "https://github.com/Shatter-Team/Shatter/wiki",
	"tracker_url": "https://github.com/Shatter-Team/Shatter/issues",
	"category": "Development",
}

import sys
import pathlib

# Set up import so that it tries to load shit from our directory without
# bitching that it can't find things.
shatter_dir = pathlib.Path(__file__).parent
sys.path.append(str(shatter_dir))

import main

def register():
	main.register()

def unregister():
	main.unregister()