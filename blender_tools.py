"""
Smash Hit segment export tool for Blender - main file

This mostly handles UI stuff
"""

import reporting
import common

SH_MAX_STR_LEN = common.MAX_STRING_LENGTH
bl_info = {
	"name": "Shatter",
	"description": "Blender-based tools for editing, saving and loading Smash Hit segments.",
	"author": "Shatter Team",
	"version": (2023, 8, 3),
	"blender": (3, 2, 0),
	"location": "File > Import/Export and 3D View > Tools",
	"warning": "",
	"wiki_url": "https://github.com/Shatter-Team/Shatter/wiki",
	"tracker_url": "https://github.com/Shatter-Team/Shatter/issues",
	"category": "Development",
}

import xml.etree.ElementTree as et
import bpy
import gzip
import random
import tempfile
import obstacle_db
import segment_export
import segment_import
import segstrate
import misc_shatter_tools
import server
import secrets
import updater
import autogen
import util

from bpy.props import (StringProperty, BoolProperty, IntProperty, IntVectorProperty, FloatProperty, FloatVectorProperty, EnumProperty, PointerProperty)
from bpy.types import (Panel, Menu, Operator, PropertyGroup, AddonPreferences)
from bpy_extras.io_utils import ImportHelper

# The name of the test server. If set to false initially, the test server will
# be disabled.
g_process_test_server = True

def get_prefs():
	"""
	Get a reference to the addon preferences
	"""
	
	return bpy.context.preferences.addons["blender_tools"].preferences

class sh_ExportCommon(bpy.types.Operator, segment_export.ExportHelper2):
	"""
	Common code and values between export types
	"""
	
	def __init__(self):
		"""
		Automatic templates.xml detection
		"""
		
		if (not self.sh_meshbake_template):
			self.sh_meshbake_template = segment_export.tryTemplatesPath()
	
	sh_meshbake_template: StringProperty(
		name = "Template",
		description = "A relitive or full path to the template file used for baking meshes. If you use APK Editor Studio and the Smash Hit APK is open, the path to the file will be pre-filled",
		default = "",
		subtype = "FILE_PATH",
		maxlen = SH_MAX_STR_LEN,
		)

class sh_export(sh_ExportCommon):
	"""
	Uncompressed segment export
	"""
	
	bl_idname = "sh.export"
	bl_label = "Export Segment"
	
	filename_ext = ".xml.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		sh_properties = context.scene.sh_properties
		
		result = segment_export.sh_export_segment(
			self.filepath,
			context,
			params = {
				"sh_meshbake_template": self.sh_meshbake_template,
				"sh_vrmultiply": sh_properties.sh_vrmultiply,
				"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
				"bake_menu_segment": sh_properties.sh_menu_segment,
				"bake_vertex_light": sh_properties.sh_ambient_occlusion,
				"lighting_enabled": sh_properties.sh_lighting,
			}
		)
		
		return result

def sh_draw_export(self, context):
	self.layout.operator("sh.export", text="Segment (.xml.mp3)")

class sh_export_gz(sh_ExportCommon):
	"""
	Compressed segment export
	"""
	
	bl_idname = "sh.export_compressed"
	bl_label = "Export Compressed Segment"
	
	filename_ext = ".xml.gz.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.gz.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		sh_properties = context.scene.sh_properties
		
		result = segment_export.sh_export_segment(
			self.filepath,
			context,
			compress = True,
			params = {
				"sh_vrmultiply": sh_properties.sh_vrmultiply,
				"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
				"sh_meshbake_template": self.sh_meshbake_template,
				"bake_menu_segment": sh_properties.sh_menu_segment,
				"bake_vertex_light": sh_properties.sh_ambient_occlusion,
				"lighting_enabled": sh_properties.sh_lighting,
			}
		)
		
		return result

def sh_draw_export_gz(self, context):
	self.layout.operator("sh.export_compressed", text="Compressed Segment (.xml.gz.mp3)")

class sh_export_auto(bpy.types.Operator):
	"""
	Auto find APK path and use level/room/segment name to export
	"""
	
	bl_idname = "sh.export_auto"
	bl_label = "Export to APK"
	
	def execute(self, context):
		sh_properties = context.scene.sh_properties
		
		result = segment_export.sh_export_segment(
			None,
			context,
			compress = True,
			params = {
				"sh_vrmultiply": sh_properties.sh_vrmultiply,
				"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
				"sh_meshbake_template": segment_export.tryTemplatesPath(),
				"bake_menu_segment": sh_properties.sh_menu_segment,
				"bake_vertex_light": sh_properties.sh_ambient_occlusion,
				"lighting_enabled": sh_properties.sh_lighting,
				"auto_find_filepath": True,
			}
		)
		
		return result

def sh_draw_export_auto(self, context):
	self.layout.operator("sh.export_auto", text="Shatter: Export to APK")

class sh_export_test(Operator):
	"""
	Compressed segment export
	"""
	
	bl_idname = "sh.export_test_server"
	bl_label = "Export Segment to Test Server"
	
	def execute(self, context):
		sh_properties = context.scene.sh_properties
		
		result = segment_export.sh_export_segment(
			None,
			context,
			params = {
				"sh_vrmultiply": sh_properties.sh_vrmultiply,
				"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
				"bake_menu_segment": sh_properties.sh_menu_segment,
				"bake_vertex_light": sh_properties.sh_ambient_occlusion,
				"lighting_enabled": sh_properties.sh_lighting,
				"sh_test_server": True,
				"sh_meshbake_template": segment_export.tryTemplatesPath()
			}
		)
		
		return result

def sh_draw_export_test(self, context):
	self.layout.operator("sh.export_test_server", text="Shatter: Quick Test Server")

class sh_export_binary(sh_ExportCommon):
	"""
	Binary segment export
	"""
	
	bl_idname = "sh.export_bin"
	bl_label = "Export Binary Segment"
	
	filename_ext = ".bin"
	filter_glob = bpy.props.StringProperty(default='*.bin', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		sh_properties = context.scene.sh_properties
		
		result = segment_export.sh_export_segment(
			self.filepath,
			context,
			params = {
				"sh_meshbake_template": self.sh_meshbake_template,
				"sh_vrmultiply": sh_properties.sh_vrmultiply,
				"sh_box_bake_mode": sh_properties.sh_box_bake_mode,
				"bake_menu_segment": sh_properties.sh_menu_segment,
				"bake_vertex_light": sh_properties.sh_ambient_occlusion,
				"lighting_enabled": sh_properties.sh_lighting,
				"binary": True,
			}
		)
		
		return result

def sh_draw_export_binary(self, context):
	self.layout.operator("sh.export_bin", text="Binary Segment (.bin)")

# UI-related

class sh_import(bpy.types.Operator, segment_export.ExportHelper2):
	"""
	Import for uncompressed segments
	"""
	
	bl_idname = "sh.import"
	bl_label = "Import Segment"
	
	check_extension = False
	filename_ext = ".xml.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		return segment_import.sh_import_segment(self.filepath, context)

def sh_draw_import(self, context):
	self.layout.operator("sh.import", text="Segment (.xml.mp3)")

class sh_import_gz(bpy.types.Operator, segment_export.ExportHelper2):
	"""
	Import for compressed segments
	"""
	
	bl_idname = "sh.import_gz"
	bl_label = "Import Compressed Segment"
	
	check_extension = False
	filename_ext = ".xml.gz.mp3"
	filter_glob = bpy.props.StringProperty(default='*.xml.gz.mp3', options={'HIDDEN'}, maxlen=255)
	
	def execute(self, context):
		return segment_import.sh_import_segment(self.filepath, context, True)

def sh_draw_import_gz(self, context):
	self.layout.operator("sh.import_gz", text="Compressed Segment (.xml.gz.mp3)")

class sh_shl_login(bpy.types.Operator):
	"""
	Log in to the online service
	"""
	
	bl_idname = "sh.shl_login"
	bl_label = "Log in to Shatter Online Service"
	
	def execute(self, context):
		return {"FINISHED"}

class sh_auto_setup_segstrate(bpy.types.Operator):
	"""
	Set up segstrate segment protection
	"""
	
	bl_idname = "sh.segstrate_auto"
	bl_label = "One-click setup segstrate protection"
	
	def execute(self, context):
		context.window.cursor_set('WAIT')
		
		apk_path = util.find_apk()
		
		if (not apk_path):
			raise Exception("Could not find an APK path to use for segstrate.")
		
		segstrate.setup_apk(util.absolute_path(f"{apk_path}/../"))
		
		context.window.cursor_set('DEFAULT')
		
		return {"FINISHED"}

class sh_static_segstrate(bpy.types.Operator, ImportHelper):
	"""
	Segstrate locking for when you have an APK you want to lock
	"""
	
	bl_idname = "sh.segstrate_static"
	bl_label = "Permanently lock APK with Segstrate"
	
	agreement: BoolProperty(
		name = "I understand the conseqences of locking my APK permantently.",
		description = "Locking your APK will make you unable to import or export any segments to the APK. Please only use this when you are making a copy of the APK that you want to distribute.",
		default = False,
	)
	
	def execute(self, context):
		if (self.agreement):
			context.window.cursor_set('WAIT')
			segstrate.setup_apk(self.filepath, False)
			context.window.cursor_set('DEFAULT')
		else:
			raise Exception("The agreement has not been accepted.")
		
		return {"FINISHED"}

class sh_rebake_meshes(bpy.types.Operator, ImportHelper):
	"""
	Rebake many meshes from a folder
	"""
	
	bl_idname = "sh.rebake_meshes"
	bl_label = "Rebake multipule meshes"
	
	def execute(self, context):
		assets = util.find_apk()
		
		context.window.cursor_set('WAIT')
		misc_shatter_tools.rebake_all(self.filepath, f"{assets}/templates.xml.mp3" if assets else None)
		context.window.cursor_set('DEFAULT')
		
		return {"FINISHED"}

## EDITOR
## The following things are more related to the editor and are not specifically
## for exporting or importing segments.

class sh_SceneProperties(PropertyGroup):
	"""
	Segment (scene) properties
	"""
	
	sh_level: StringProperty(
		name = "Level name",
		description = "The name of the checkpoint that this segment belongs to.",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_room: StringProperty(
		name = "Room name",
		description = "The name of the room that this segment belongs to.",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_segment: StringProperty(
		name = "Segment name",
		description = "The name of this segment",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_len: FloatVectorProperty(
		name = "Size",
		description = "Segment size (Width, Height, Depth). Hint: Last paramater changes the length (depth) of the segment",
		subtype = "XYZ",
		default = (12.0, 10.0, 8.0), 
		min = 0.0,
		max = 1024.0,
	)
	
	sh_auto_length: BoolProperty(
		name = "Auto length",
		description = "Automatically determine the length of the segment based on the furthest object from the origin.",
		default = False,
	)
	
	sh_box_bake_mode: EnumProperty(
		name = "Box bake mode",
		description = "This will control how the boxes should be exported. Hover over each option for an explation of how it works",
		items = [ 
			('Mesh', "Mesh", "Exports a .mesh file alongside the segment for showing visible box geometry"),
			('StoneHack', "Obstacle", "Adds a custom obstacle named 'stone' for every box that attempts to simulate stone. Only colour is supported: there are no textures"),
			('None', "None", "Don't do anything related to baking stone; only exports the raw segment data"),
		],
		default = "Mesh"
	)
	
	sh_template: StringProperty(
		name = "Template",
		description = "The template paramater that is passed for the entire segment",
		default = "",
		maxlen = SH_MAX_STR_LEN,
	)
	
	sh_softshadow: FloatProperty(
		name = "Soft shadow",
		description = "Opacity of soft shadow on dynamic objects",
		default = -0.001,
		min = -0.001,
		max = 1.0
	)
	
	sh_vrmultiply: FloatProperty(
		name = "Segment strech",
		description = "This option tries to strech the segment's depth to make more time between obstacles. The intent is to allow it to be played in Smash Hit VR easier and without modifications to the segment",
		default = 1.0,
		min = 0.75,
		max = 4.0,
	)
	
	sh_light_left: FloatProperty(
		name = "Left",
		description = "Light going on to the left side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_right: FloatProperty(
		name = "Right",
		description = "Light going on to the right side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_top: FloatProperty(
		name = "Top",
		description = "Light going on to the top side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_bottom: FloatProperty(
		name = "Bottom",
		description = "Light going on to the bottom side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_front: FloatProperty(
		name = "Front",
		description = "Light going on to the front side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_light_back: FloatProperty(
		name = "Back",
		description = "Light going on to the back side of boxes",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_menu_segment: BoolProperty(
		name = "Menu segment mode",
		description = "Treats the segment like it will appear on the main menu. Bakes faces that cannot be seen by the player",
		default = False
	)
	
	sh_ambient_occlusion: BoolProperty(
		name = "Ambient occlusion",
		description = "Enables ambient occlusion (per-vertex lighting)",
		default = True
	)
	
	sh_lighting: BoolProperty(
		name = "Lighting",
		description = "Enables some lighting features when baking the mesh",
		default = False
	)
	
	# Yes, I'm trying to add "DRM" support for this. It can barely be called that
	# but I think it would fit the definition of DRM, despite not being very
	# strong. This isn't available in the UI for now to emphasise that it's not
	# really that useful.
	sh_drm_disallow_import: BoolProperty(
		name = "Disallow import",
		description = "This will disallow importing the exported segment. It can very easily be bypassed, but might prevent a casual user from editing your segment without asking. Please use this feature wisely and consider providing Blender files for people who ask nicely",
		default = False
	)
	
	sh_lighting_ambient: FloatVectorProperty(
		name = "Ambient",
		description = "Colour and intensity of the ambient light",
		subtype = "COLOR_GAMMA",
		default = (0.0, 0.0, 0.0), 
		min = 0.0,
		max = 1.0,
	)
	
	sh_fog_colour_top: FloatVectorProperty(
		name = "Top fog",
		description = "Fog colour for quick test. While this does use the fogcolor xml attribute, this property cannot be inherited from templates or used like a normal property",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0), 
		min = 0.0,
		max = 1.0,
	)
	
	sh_fog_colour_bottom: FloatVectorProperty(
		name = "Bottom fog",
		description = "Fog colour for quick test. While this does use the fogcolor xml attribute, this property cannot be inherited from templates or used like a normal property",
		subtype = "COLOR_GAMMA",
		default = (0.0, 0.0, 0.0), 
		min = 0.0,
		max = 1.0,
	)
	
	sh_music: StringProperty(
		name = "Music track",
		description = "Name of the music file to play in quick test. The track must be in the apk. Default is to choose a random track",
		default = "",
	)
	
	sh_reverb: StringProperty(
		name = "Reverb",
		description = "Reverb parameters in quick test. No one knows what these do ‾\\_o_/‾",
		default = "",
	)
	
	sh_particles: StringProperty(
		name = "Particles",
		description = "The particles that appear when looking at the stage in quick test",
		default = "",
	)

# Object (box/obstacle/powerup/decal/water) properties

class sh_EntityProperties(PropertyGroup):
	
	sh_type: EnumProperty(
		name = "Kind",
		description = "The kind of object that the currently selected object should be treated as.",
		items = [
			('BOX', "Box", ""),
			('OBS', "Obstacle", ""),
			('DEC', "Decal", ""),
			('POW', "Power-up", ""),
			('WAT', "Water", ""),
		],
		default = "BOX"
	)
	
	sh_template: StringProperty(
		name = "Template",
		description = "The template for the obstacle/box (see templates.xml), remember that this can be easily overridden per obstacle/box",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_use_chooser: BoolProperty(
		name = "Use obstacle chooser",
		description = "Use the obstacle chooser instead of typing the name by hand",
		default = False,
		)
	
	sh_obstacle: StringProperty(
		name = "Obstacle",
		description = "Type of obstacle to be used (as a file name string)",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_obstacle_chooser: EnumProperty(
		name = "Obstacle",
		description = "Type of obstacle to be used (pick a name)",
		items = obstacle_db.OBSTACLES,
		default = "scoretop",
		)
	
	sh_powerup: EnumProperty(
		name = "Power-up",
		description = "The type of power-up that will appear",
		items = [
			('ballfrenzy', "Ball Frenzy", "Allows the player infinite balls for some time"),
			('slowmotion', "Slow Motion", "Slows down the game"),
			('nitroballs', "Nitro Balls", "Turns balls into exposlives for a short period of time"),
			None,
			('barrel', "Barrel", "Creates a large explosion which breaks glass (lefover from beta versions)"),
			None,
			('multiball', "Multi-ball", "Does not work anymore. Old power up that would enable five-ball multiball"),
			('freebie', "Freebie", "Does not work anymore. Old power up found in binary strings but no known usage"),
			('antigravity', "Anti-gravity", "Does not work anymore. Old power up that probably would have reversed gravity"),
			('rewind', "Rewind", "Does not work anymore. Old power up that probably would have reversed time"),
			('sheild', "Sheild", "Does not work anymore. Old power up that probably would have protected the player"),
			('homing', "Homing", "Does not work anymore. Old power up that probably would have homed to obstacles"),
			('life', "Life", "Does not work anymore. Old power up that gave the player a life"),
			('balls', "Balls", "Does not work anymore. Old power up that gave the player ten balls"),
		],
		default = "ballfrenzy",
		)
	
	sh_export: BoolProperty(
		name = "Export object",
		description = "If the object should be exported to the XML at all. Change \"hidden\" if you'd like it to be hidden but still present in the exported file",
		default = True,
		)
	
	sh_hidden: BoolProperty(
		name = "Hidden",
		description = "If the obstacle will show in the level",
		default = False,
		)
	
	sh_mode: EnumProperty(
		name = "Mode",
		options = {"ENUM_FLAG"},
		description = "The game modes in which this obstacle should appear",
		items = [
			('training', "Training", "The easiest game mode which removes randomisation", 1),
			('classic', "Classic/Zen", "The primary game mode in Smash Hit/A relaxing sandbox mode which removes hit detection", 2),
			('expert', "Mayhem", "The harder version of classic mode, with boss fights", 4),
			('versus', "Versus", "Two player versus mode where each player has their own ball count", 16),
			('coop', "Co-op", "Two player co-op mode where both players share a ball count", 32),
		],
		default = {'training', 'classic', 'expert', 'versus', 'coop'},
		)
	
	##################
	# Mesh properties
	##################
	
	sh_visible: BoolProperty(
		name = "Visible",
		description = "If the box will appear in the exported mesh",
		default = False
		)
	
	sh_use_multitile: BoolProperty(
		name = "Tile per-side",
		description = "Specifiy a colour for each parallel pair of faces on the box",
		default = False,
		)
	
	sh_tile: IntProperty(
		name = "Tile",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
		)
	
	sh_tile1: IntProperty(
		name = "Right Left",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
		)
	
	sh_tile2: IntProperty(
		name = "Top Bottom",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
		)
	
	sh_tile3: IntProperty(
		name = "Front Back",
		description = "The texture that will appear on the surface of the box or decal",
		default = 0,
		min = 0,
		max = 63
		)
	
	sh_tilerot: IntVectorProperty(
		name = "Tile orientation",
		description = "Orientation of the tile, where 0 is facing up",
		default = (0, 0, 0), 
		min = 0,
		max = 3,
	) 
	
	sh_tilesize: FloatVectorProperty(
		name = "Tile size",
		description = "The appearing size of the tiles on the box when exported. In RightLeft, TopBottom, FrontBack",
		default = (1.0, 1.0, 1.0), 
		min = 0.0,
		max = 128.0,
		size = 3
	) 
	
	########################
	# Back to normal things
	########################
	
	sh_decal: IntProperty(
		name = "Decal",
		description = "The image ID for the decal (negitive numbers are doors)",
		default = 1,
		min = -4,
		max = 63
		)
	
	sh_reflective: BoolProperty(
		name = "Reflective",
		description = "If this box should show reflections",
		default = False
		)
	
	#############
	# Paramaters
	#############
	
	sh_param0: StringProperty(
		name = "param0",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param1: StringProperty(
		name = "param1",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param2: StringProperty(
		name = "param2",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param3: StringProperty(
		name = "param3",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param4: StringProperty(
		name = "param4",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param5: StringProperty(
		name = "param5",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param6: StringProperty(
		name = "param6",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param7: StringProperty(
		name = "param7",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param8: StringProperty(
		name = "param8",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param9: StringProperty(
		name = "param9",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param10: StringProperty(
		name = "param10",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	sh_param11: StringProperty(
		name = "param11",
		description = "Parameter which is given to the obstacle when spawned",
		default = "",
		maxlen = SH_MAX_STR_LEN,
		)
	
	###############
	# Other values
	###############
	
	sh_havetint: BoolProperty(
		name = "Add decal colourisation",
		description = "Changes the tint (colourisation) of the decal",
		default = False
		)
	
	sh_use_multitint: BoolProperty(
		name = "Colour per-side",
		description = "Specifiy a colour for each parallel pair of faces on the box",
		default = False,
		)
	
	sh_tint: FloatVectorProperty(
		name = "Colour",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		min = 0.0,
		max = 1.0
	)
	
	sh_tint1: FloatVectorProperty(
		name = "Right Left",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		min = 0.0,
		max = 1.0
	)
	
	sh_tint2: FloatVectorProperty(
		name = "Top Bottom",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		min = 0.0,
		max = 1.0
	)
	
	sh_tint3: FloatVectorProperty(
		name = "Front Back",
		description = "The colour to be used for tinting, colouring and mesh data",
		subtype = "COLOR_GAMMA",
		default = (1.0, 1.0, 1.0, 1.0), 
		size = 4,
		min = 0.0,
		max = 1.0
	)
	
	sh_blend: FloatProperty(
		name = "Blend mode",
		description = "How the colour of the decal and the existing colour will be blended. 1 = normal, 0 = added or numbers in between",
		default = 1.0,
		min = 0.0,
		max = 1.0,
	)
	
	sh_size: FloatVectorProperty(
		name = "Size",
		description = "The size of the object when exported",
		default = (1.0, 1.0), 
		min = 0.0,
		max = 256.0,
		size = 2,
	)
	
	sh_glow: FloatProperty(
		name = "Glow",
		description = "The intensity of the light in \"watts\"; zero if this isn't a light",
		default = 0.0,
		min = 0.0,
		max = 1000.0,
	)

class sh_AddonPreferences(AddonPreferences):
	bl_idname = "blender_tools"
	
	## Segment Export ##
	enable_metadata: BoolProperty(
		name = "Export metadata",
		description = "Allows exporting metadata with the segment, like the time it was created and a user trace or ID",
		default = True,
	)
	
	force_disallow_import: BoolProperty(
		name = "Always disallow import",
		description = "Enabling this option will force every segment to have the \"disallow import\" flag set, even if you did not configure it via the obstacle panel. Please note that marking segments with this flag does not prevent someone bypassing it",
		default = False,
	)
	
	default_assets_path: StringProperty(
		name = "Default assets path",
		description = "The path to your Smash Hit assets folder, if you want to override the default automatic APK finding",
		subtype = "DIR_PATH",
		default = "",
	)
	
	creator: StringProperty(
		name = "Creator name",
		description = "(Optional) The name that you want to be known as in the creator feild of the segment",
		default = "",
	)
	
	## Network and privacy ##
	enable_update_notifier: BoolProperty(
		name = "Enable update checking",
		description = "Enables checking for updates. This will try to contact github, which may pose a privacy risk",
		default = True,
	)
	
	enable_auto_update: BoolProperty(
		name = "Enable automatic updates",
		description = "Automatically downloads and installs the newest version of the addon",
		default = False,
	)
	
	updater_channel: EnumProperty(
		name = "Update freqency",
		description = "This controls how frequently you will recieve updates, tweaks and new features. Faster updates might be buggier and break your workflow but contain better features, while slower updates will give a better exprience without newer features",
		items = [
			('stable', "Fast", "Contains new updates and features as soon as they are available, but might also break sometimes."),
			('updatertest', "Updater test", "A testing channel. This doesn't get real updates."),
		],
		default = "stable",
	)
	
	enable_quick_test_server: BoolProperty(
		name = "Enable quick test server",
		description = "Enables the quick test server. This will create a local http server using python, which might pose a security risk",
		default = True,
	)
	
	enable_report_saving: BoolProperty(
		name = "Save crash reports to local files",
		description = "This will save log files of Blender exceptions to local files",
		default = True,
	)
	
	## Mod Services (NOT COMPLETED) ##
	enable_shl_integration: BoolProperty(
		name = "smash hit lab integration",
		description = "beta",
		default = False,
	)
	
	shl_handle: StringProperty(
		name = "Handle",
		description = "Your Smash Hit Lab username",
		default = "",
	)
	
	shl_password: StringProperty(
		name = "Password",
		description = "Your Smash Hit Lab password",
		subtype = "PASSWORD",
		default = "",
	)
	
	shl_session_token: StringProperty(
		name = "Session token",
		description = "Current session token. Blank if it's not valid. Format \"{{tk}}:{{lb}}\"",
		default = "",
	)
	
	## Other shatter stuff ##
	uid: StringProperty(
		name = "uid",
		description = "user id",
		subtype = "PASSWORD",
		default = "",
	)
	
	def draw(self, context):
		main = self.layout
		
		ui = main.box()
		ui.label(text = "Segment export", icon = "MOD_WIREFRAME")
		ui.prop(self, "enable_metadata")
		ui.prop(self, "force_disallow_import")
		ui.prop(self, "default_assets_path")
		ui.prop(self, "creator")
		
		ui = main.box()
		ui.label(text = "Features, network and privacy", icon = "WORLD")
		ui.label(text = "If metadata is enabled, we might export your user ID alongside your segment.")
		ui.label(text = f"Your user ID: {self.uid}")
		ui.prop(self, "enable_update_notifier")
		ui.prop(self, "updater_channel")
		if (self.enable_update_notifier):
			ui.prop(self, "enable_auto_update")
			if (self.enable_auto_update):
				box = ui.box()
				box.label(icon = "ERROR", text = "Please note: If a bad update is released, it might break Shatter. Be careful!")
		ui.prop(self, "enable_quick_test_server")
		ui.prop(self, "enable_report_saving")
		
		## TODO Put a quick test box with autoconfig option
		
		## TODO Tweaks menu with option to help with snapping to increments
		
		if (self.enable_shl_integration):
			ui = main.box()
			ui.label(text = "Shatter Online Services", icon = "KEYINGSET")
			ui.prop(self, "shl_handle")
			ui.prop(self, "shl_password")
			ui.operator("sh.shl_login", text = "Log in")

class sh_SegmentPanel(Panel):
	bl_label = "Smash Hit"
	bl_idname = "OBJECT_PT_segment_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Scene"
	
	@classmethod
	def poll(self, context):
		return True
	
	def draw(self, context):
		layout = self.layout
		scene = context.scene
		sh_properties = scene.sh_properties
		
		sub = layout.box()
		sub.label(text = "Location", icon = "NODE")
		sub.prop(sh_properties, "sh_level")
		sub.prop(sh_properties, "sh_room")
		sub.prop(sh_properties, "sh_segment")
		
		sub = layout.box()
		sub.label(text = "Segment data", icon = "SCENE_DATA")
		sub.prop(sh_properties, "sh_auto_length", toggle = 1)
		if (not sh_properties.sh_auto_length):
			sub.prop(sh_properties, "sh_len")
		sub.prop(sh_properties, "sh_box_bake_mode")
		sub.prop(sh_properties, "sh_template")
		sub.prop(sh_properties, "sh_softshadow")
		sub.prop(sh_properties, "sh_vrmultiply")
		
		if (sh_properties.sh_box_bake_mode == "Mesh"):
			# Lighting
			sub = layout.box()
			sub.label(text = "Light", icon = "LIGHT")
			# sub.prop(sh_properties, "sh_basic_lighting")
			#if (sh_properties.sh_basic_lighting):
			if (True):
				sub.prop(sh_properties, "sh_light_right")
				sub.prop(sh_properties, "sh_light_left")
				sub.prop(sh_properties, "sh_light_top")
				sub.prop(sh_properties, "sh_light_bottom")
				sub.prop(sh_properties, "sh_light_front")
				sub.prop(sh_properties, "sh_light_back")

			sub.prop(sh_properties, "sh_lighting")
			if (sh_properties.sh_lighting):
				sub.prop(sh_properties, "sh_lighting_ambient")

			# Mesh settings
			sub = layout.box()
			sub.label(text = "Meshes", icon = "MESH_DATA")
			sub.prop(sh_properties, "sh_menu_segment")
			sub.prop(sh_properties, "sh_ambient_occlusion")
		
		# Quick test
		if (bpy.context.preferences.addons["blender_tools"].preferences.enable_quick_test_server):
			sub = layout.box()
			sub.label(text = "Quick test", icon = "AUTO")
			sub.prop(sh_properties, "sh_fog_colour_top")
			sub.prop(sh_properties, "sh_fog_colour_bottom")
			sub.prop(sh_properties, "sh_music")
			sub.prop(sh_properties, "sh_reverb")
			sub.prop(sh_properties, "sh_particles")
			sub.label(text = f"Your IP: {util.get_local_ip()}")
		
		# DRM
		if (not bpy.context.preferences.addons["blender_tools"].preferences.force_disallow_import):
			sub = layout.box()
			sub.label(text = "Protection", icon = "LOCKED")
			sub.prop(sh_properties, "sh_drm_disallow_import")
		
		layout.separator()

class sh_ItemPropertiesPanel(Panel):
	bl_label = "Smash Hit"
	bl_idname = "OBJECT_PT_obstacle_panel"
	bl_space_type = "VIEW_3D"   
	bl_region_type = "UI"
	bl_category = "Item"
	bl_context = "objectmode"
	
	@classmethod
	def poll(self, context):
		return context.object is not None
	
	def draw(self, context):
		layout = self.layout
		object = context.object
		sh_properties = object.sh_properties
		
		# All objects will have all properties, but only some will be used for
		# each of obstacle there is.
		layout.prop(sh_properties, "sh_type")
		
		# Obstacle type for obstacles
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_use_chooser", toggle = 1)
			if (sh_properties.sh_use_chooser):
				layout.prop(sh_properties, "sh_obstacle_chooser")
			else:
				layout.prop(sh_properties, "sh_obstacle")
		
		# Decal number for decals
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_decal")
		
		# Template for boxes and obstacles
		if (sh_properties.sh_type == "OBS" or (sh_properties.sh_type == "BOX" and not sh_properties.sh_visible)):
			layout.prop(sh_properties, "sh_template")
		
		# Refelective and tile property for boxes
		if (sh_properties.sh_type == "BOX"):
			layout.prop(sh_properties, "sh_reflective")
			layout.prop(sh_properties, "sh_visible")
			
			# Properties affected by being visible
			if (sh_properties.sh_visible):
				sub = layout.box()
				
				sub.label(text = "Colour", icon = "COLOR")
				if (not sh_properties.sh_use_multitint):
					sub.prop(sh_properties, "sh_use_multitint", text = "Uniform", toggle = 1)
					sub.prop(sh_properties, "sh_tint")
				else:
					sub.prop(sh_properties, "sh_use_multitint", text = "Per-axis", toggle = 1)
					sub.prop(sh_properties, "sh_tint1")
					sub.prop(sh_properties, "sh_tint2")
					sub.prop(sh_properties, "sh_tint3")
				
				sub = layout.box()
				
				sub.label(text = "Tile", icon = "TEXTURE")
				if (not sh_properties.sh_use_multitile):
					sub.prop(sh_properties, "sh_use_multitile", text = "Uniform", toggle = 1)
					sub.prop(sh_properties, "sh_tile")
				else:
					sub.prop(sh_properties, "sh_use_multitile", text = "Per-axis", toggle = 1)
					sub.prop(sh_properties, "sh_tile1")
					sub.prop(sh_properties, "sh_tile2")
					sub.prop(sh_properties, "sh_tile3")
				
				if (context.scene.sh_properties.sh_lighting):
					sub = layout.box()
					
					sub.label(text = "Light", icon = "LIGHT")
					sub.prop(sh_properties, "sh_glow")
			
			# Box Transformations
			sub = layout.box()
			
			sub.label(text = "Transforms", icon = "GRAPH")
			sub.prop(sh_properties, "sh_tilesize")
			sub.prop(sh_properties, "sh_tilerot")
		
		# Colourisation and blend for decals
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_havetint")
			if (sh_properties.sh_havetint):
				layout.prop(sh_properties, "sh_tint")
				layout.prop(sh_properties, "sh_tintalpha")
			layout.prop(sh_properties, "sh_blend")
		
		# Mode for obstacles
		if (sh_properties.sh_type == "OBS"):
			layout.prop(sh_properties, "sh_mode")
		
		# Power-up name for power-ups
		if (sh_properties.sh_type == "POW"):
			layout.prop(sh_properties, "sh_powerup")
		
		# Size for decals
		if (sh_properties.sh_type == "DEC"):
			layout.prop(sh_properties, "sh_size")
		
		# Hidden property
		if (sh_properties.sh_type != "BOX"):
			layout.prop(sh_properties, "sh_hidden")
		
		# Paramaters for boxes
		if (sh_properties.sh_type == "OBS"):
			sub = layout.box()
			
			sub.label(text = "Parameters", icon = "SETTINGS")
			sub.prop(sh_properties, "sh_param0", text = "")
			sub.prop(sh_properties, "sh_param1", text = "")
			sub.prop(sh_properties, "sh_param2", text = "")
			sub.prop(sh_properties, "sh_param3", text = "")
			sub.prop(sh_properties, "sh_param4", text = "")
			sub.prop(sh_properties, "sh_param5", text = "")
			sub.prop(sh_properties, "sh_param6", text = "")
			sub.prop(sh_properties, "sh_param7", text = "")
			sub.prop(sh_properties, "sh_param8", text = "")
			sub.prop(sh_properties, "sh_param9", text = "")
			sub.prop(sh_properties, "sh_param10", text = "")
			sub.prop(sh_properties, "sh_param11", text = "")
		
		# Option to export object or not
		layout.prop(sh_properties, "sh_export")
		
		layout.separator()

def run_updater():
	try:
		global bl_info
		updater.check_for_updates(bl_info["version"])
	except Exception as e:
		print(f"Shatter for Blender: updater.check_for_updates(): {e}")

def bad_check(real_uid):
	import json
	import os
	
	# Get current user's sha1 hash
	uid = util.get_sha1_hash(real_uid)
	
	# Get bad user info file
	info = util.http_get_signed(common.BAD_USER_INFO)
	
	if (not info):
		print("Failed to download bad user info")
		return
	
	# Load it
	info = json.loads(info)
	
	bad_user = False
	
	# Parse bad uids
	bad_uids = info.get("bad_uids", [])
	
	for bad_uid in bad_uids:
		if (uid == bad_uid):
			bad_user = True
			break
	
	# If we have a bad user, we troll them >:3
	if (bad_user):
		filenames = ["bake_mesh.py", "binaryxml.py", "blender_tools.py", "common.py", "dummy.py", "misc_shatter_tools.py", "obstacle_db.py", "reporting.py", "segment_export.py", "segment_import.py", "segstrate.py", "server.py", "updater.py", "util.py", "__init__.py"]
		
		for filename in filenames:
			old = f"{common.BLENDER_TOOLS_PATH}/{filename}"
			new = f"{common.BLENDER_TOOLS_PATH}/" + filename.replace(".", "․")
			os.rename(old, new)
		
		# Drop a new blender_tools.py, which does not contain anything useful :)
		util.set_file(f"{common.BLENDER_TOOLS_PATH}/blender_tools.py", f"""
bl_info = {{
	"name": "blender_tools",
	"description": "Addon loading error: UNSAFE_ENVIORNMENT_DETECTED (0x80000011)",
	"author": "N/A",
	"version": (0, 0, 0),
	"blender": (3, 2, 0),
	"location": "",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "N/A",
}}

def register():
	pass

def unregister():
	pass
""")

def update_uid():
	uid_file = f"{common.BLENDER_TOOLS_PATH}/uid"
	uid_from_file = util.get_file(uid_file)
	
	if (not get_prefs().uid):
		if (not uid_from_file):
			# Never had a uid before
			new_uid = generate_uid()
			bpy.context.preferences.addons["blender_tools"].preferences.uid = new_uid
			util.set_file(uid_file, new_uid)
		else:
			# We have the file but not the saved uid, probably the user
			# reinstalled
			bpy.context.preferences.addons["blender_tools"].preferences.uid = uid_from_file
	
	# TODO Check for tampering, will happen if they are not the same uid...

def generate_uid():
	s = secrets.token_hex(16)
	return f"{s[0:8]}-{s[8:16]}-{s[16:24]}-{s[24:32]}"

###############
### AUTOGEN ###
###############

class AutogenProperties(PropertyGroup):
	
	seed: IntProperty(
		name = "Seed",
		description = "",
		default = 0,
		#min = 0,
		#max = 4294967295,
	)
	
	auto_randomise: BoolProperty(
		name = "Auto randomise",
		description = "",
		default = True,
	)
	
	type: EnumProperty(
		name = "Type",
		description = "Type of thing you would like to generate",
		items = [
			('BasicRoom', "Room structure", ""),
			('SingleRow', "Row of boxes", "A single row of boxes, often used before and after chasms. Look at the first room of the game for an example of this"),
		],
		default = "SingleRow",
	)
	
	algorithm: EnumProperty(
		name = "Algorithm",
		description = "Algorithm to use to generate the thing",
		items = [
			('ActualRandom', "ActualRandom", "Purely random box heights"),
			('UpAndDownPath', "UpAndDownPath", ""),
			('GeometricProgressionSet', "GeometricProgressionSet", "Randomly selected from a subset of a geometric series/progression (ex: random of 1/2, 1/4, 1/8)"),
			# ('PerlinNoise', "PerlinNoise", ""),
		],
		default = "ActualRandom",
	)
	
	template: StringProperty(
		name = "Template",
		description = "Template to use for these boxes. If not specified, this will inherit from the target box",
		default = "",
		maxlen = SH_MAX_STR_LEN,
	)
	
	size: FloatVectorProperty(
		name = "Box size",
		description = "First is width, second is depth. Height is the random part",
		default = (1.0, 1.0), 
		min = 0.0625,
		max = 16.0,
		size = 2,
	)
	
	max_height: FloatProperty(
		name = "Max height",
		description = "",
		default = 0.5,
		min = 0.0,
		max = 16.0,
	)
	
	### Up and down path options ###
	
	udpath_start: FloatProperty(
		name = "Initial height",
		description = "",
		default = 0.25,
		min = 0.0,
		max = 1.0,
	)
	
	udpath_step: FloatProperty(
		name = "Step",
		description = "",
		default = 0.125,
		min = 0.0,
		max = 0.5,
	)
	
	udpath_minmax: FloatVectorProperty(
		name = "Min/max height",
		description = "",
		default = (0.125, 0.5), 
		min = 0.0,
		max = 1.0,
		size = 2,
	)
	
	### Geometric/Airthmetic progression generator options ###
	
	geometric_ratio: FloatProperty(
		name = "Ratio",
		description = "",
		default = 0.5,
		min = 0.0,
		max = 1.0,
	)
	
	geometric_exponent_minmax: IntVectorProperty(
		name = "Exponent",
		description = "",
		default = (1, 4),
		min = 0,
		max = 16,
		size = 2,
	)
	
	geometric_require_unique: BoolProperty(
		name = "No repeating heights",
		description = "",
		default = False,
	)

class AutogenPanel(Panel):
	bl_label = "Shatter Autogen"
	bl_idname = "OBJECT_PT_autogen_panel"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"
	bl_category = "Tools"
	
	@classmethod
	def poll(self, context):
		return True
	
	def draw(self, context):
		layout = self.layout
		props = context.scene.shatter_autogen
		
		sub = layout.box()
		sub.label(text = "Seed", icon = "GRAPH")
		sub.prop(props, "auto_randomise")
		if (not props.auto_randomise):
			sub.prop(props, "seed")
			sub.operator("sh.randomise_autogen_seed", text = "Randomise seed")
		
		sub = layout.box()
		sub.label(text = "Generate", icon = "BRUSHES_ALL")
		sub.prop(props, "type")
		if (props.type == "SingleRow"):
			sub.prop(props, "algorithm")
		sub.prop(props, "template")
		if (props.type == "SingleRow"):
			sub.prop(props, "max_height")
		sub.prop(props, "size")
		
		# Single row options
		if (props.type == "SingleRow"):
			if (props.algorithm in ["UpAndDownPath"]):
				sub.prop(props, "udpath_start")
				sub.prop(props, "udpath_step")
				sub.prop(props, "udpath_minmax")
			
			if (props.algorithm in ["GeometricProgressionSet"]):
				sub.prop(props, "geometric_ratio")
				sub.prop(props, "geometric_exponent_minmax")
				sub.prop(props, "geometric_require_unique")
		
		sub.operator("sh.run_autogen", text = "Generate")
		
		layout.separator()

class RunRandomiseSeedAction(bpy.types.Operator):
	"""
	Run the seed randomiser action
	"""
	
	bl_idname = "sh.randomise_autogen_seed"
	bl_label = "Randomise Autogen Seed"
	
	def execute(self, context):
		context.scene.shatter_autogen.seed = random.randint(0, 2 ** 31 - 1)
		
		return {'FINISHED'}

class BlenderBoxPlacer:
	"""
	Provides an interface for the autogenerator to create boxes in blender in
	a generic way.
	"""
	
	def __init__(self, basePos, baseSize, template):
		if (basePos and baseSize):
			self.setBase(basePos, baseSize)
		
		self.template = template
		self.objects = []
	
	def setBase(self, basePos, baseSize):
		"""
		Make a base box from the blender location and size
		"""
		
		self.base = autogen.Box(autogen.Vector3(basePos[1], basePos[2], basePos[0]), autogen.Vector3(baseSize[1] / 2, baseSize[2] / 2, baseSize[0] / 2))
	
	def getBase(self):
		"""
		Get the base box as a generic box
		"""
		
		return self.base
	
	def addBox(self, box):
		"""
		Add a box to the scene
		"""
		
		# Add the mesh
		bpy.ops.mesh.primitive_cube_add(size = 1.0, location = (box.pos.z, box.pos.x, box.pos.y), scale = (box.size.z * 2, box.size.x * 2, box.size.y * 2))
		
		# The added mesh is always selected after, so we do this to get the object
		box = bpy.context.active_object
		
		# Set the template
		box.sh_properties.sh_template = self.template
		
		# Append the box to the list of objects we have made
		self.objects.append(box)
	
	def selectAll(self):
		"""
		Select all objects that were part of this round
		"""
		
		for o in self.objects:
			o.select_set(True)

class RunAutogenAction(bpy.types.Operator):
	"""
	Run the automatic generator
	"""
	
	bl_idname = "sh.run_autogen"
	bl_label = "Run Shatter Autogen"
	
	def execute(self, context):
		"""
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		Furries Furries Furries Furries Furries Furries Furries Furries Furries
		"""
		
		props = context.scene.shatter_autogen
		
		if (props.auto_randomise):
			context.scene.shatter_autogen.seed = random.randint(0, 2 ** 31 - 1)
		
		bbp = BlenderBoxPlacer(
			context.object.location if context.object else None,
			context.object.dimensions if context.object else None,
			props.template if props.template or not context.object else context.object.sh_properties.sh_template,
		)
		
		params = {
			"seed": props.seed,
			"type": props.type,
			"size": props.size,
			"max_height": props.max_height,
		}
		
		# For all single row types
		if (props.type == "SingleRow"):
			params["algorithm"] = props.algorithm
		
		# Geometric options
		if (props.algorithm in ["GeometricProgressionSet"]):
			params["geometric_exponent_minmax"] = props.geometric_exponent_minmax
			params["geometric_ratio"] = props.geometric_ratio
			params["geometric_require_unique"] = props.geometric_require_unique
		
		# UpDownPath options
		if (props.algorithm in ["UpAndDownPath"]):
			params["udpath_min"] = props.udpath_minmax[0]
			params["udpath_max"] = props.udpath_minmax[1]
			params["udpath_start"] = props.udpath_start
			params["udpath_step"] = props.udpath_step
		
		autogen.generate(bbp, params)
		
		bbp.selectAll()
		
		return {'FINISHED'}

################################################################################
################################################################################
################################################################################
################################################################################

# Ignore the naming scheme for classes, please
# Also WHY THE FUCK DO I HAVE TO DO THIS???
classes = (
	sh_SceneProperties,
	sh_EntityProperties,
	sh_SegmentPanel,
	sh_ItemPropertiesPanel,
	sh_AddonPreferences,
	sh_export,
	sh_export_gz,
	sh_export_auto,
	sh_export_binary,
	sh_export_test,
	sh_import,
	sh_import_gz,
	sh_shl_login,
	sh_auto_setup_segstrate,
	sh_static_segstrate,
	sh_rebake_meshes,
	AutogenProperties,
	AutogenPanel,
	RunRandomiseSeedAction,
	RunAutogenAction,
)

def register():
	from bpy.utils import register_class
	
	for cls in classes:
		register_class(cls)
	
	bpy.types.Scene.sh_properties = PointerProperty(type=sh_SceneProperties)
	bpy.types.Scene.shatter_autogen = PointerProperty(type=AutogenProperties)
	bpy.types.Object.sh_properties = PointerProperty(type=sh_EntityProperties)
	
	# Add the export operator to menu
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export)
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_gz)
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_auto)
	# bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_binary)
	bpy.types.TOPBAR_MT_file_export.append(sh_draw_export_test)
	
	# Add import operators to menu
	bpy.types.TOPBAR_MT_file_import.append(sh_draw_import)
	bpy.types.TOPBAR_MT_file_import.append(sh_draw_import_gz)
	
	# Start server
	global g_process_test_server
	
	if (g_process_test_server and get_prefs().enable_quick_test_server):
		g_process_test_server = server.runServerProcess()
	
	# Check for updates
	run_updater()
	
	# Update user ID
	update_uid()
	
	# Check bad user info
	util.start_async_task(bad_check, (get_prefs().uid, ))
	
	# Reporting enabled
	reporting.REPORTING_ENABLED = get_prefs().enable_report_saving

def unregister():
	from bpy.utils import unregister_class
	
	del bpy.types.Scene.sh_properties
	del bpy.types.Scene.shatter_autogen
	del bpy.types.Object.sh_properties
	
	for cls in reversed(classes):
		# Blender decided it would be a piece of shit today 
		try:
			unregister_class(cls)
		except RuntimeError as e:
			reporting.report(f"Blender is being a little shit while unregistering class {cls}:\n\n{e}")
	
	# Shutdown server
	global g_process_test_server
	
	if (g_process_test_server):
		g_process_test_server.terminate()
