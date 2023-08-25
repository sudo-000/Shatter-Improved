"""
Blender-specific utilities
"""

import os
import os.path as ospath
import pathlib
import tempfile
import bpy

def find_apk(*, no_override = False):
	"""
	Find the path to an APK
	"""
	
	# Search for templates.xml (how we find the APK) and set path
	path = ""
	
	# If the user has set an override path, then just return that if it exists
	override = bpy.context.preferences.addons["blender_tools"].preferences.default_assets_path
	
	if (not no_override and override and ospath.exists(override)):
		return override
	
	### Try to find from APK Editor Studio ###
	
	try:
		# Get the search path
		search_path = tempfile.gettempdir() + "/apk-editor-studio/apk"
		
		# Enumerate files
		dirs = os.listdir(search_path)
		
		for d in dirs:
			cand = str(os.path.abspath(search_path + "/" + d + "/assets/templates.xml.mp3"))
			
			print("Trying the path:", cand)
			
			if ospath.exists(cand):
				path = str(pathlib.Path(cand).parent)
				break
	except FileNotFoundError:
		print("Smash Hit Tools: No APK Editor Studio folder found.")
	
	print("Final apk path:", path)
	
	return path

def add_box(pos, size):
	"""
	Add a box to the scene and return reference to it
	
	See: https://blender.stackexchange.com/questions/2285/how-to-get-reference-to-objects-added-by-an-operator
	"""
	
	bpy.ops.mesh.primitive_cube_add(size = 1.0, location = (pos[0], pos[1], pos[2]), scale = (size[0] * 2, size[1] * 2, size[2] * 2))
	
	return bpy.context.active_object

def add_empty():
	"""
	Add an empty object and return a reference to it
	"""
	
	o = bpy.data.objects.new("empty", None)
	
	bpy.context.scene.collection.objects.link(o)
	
	o.empty_display_size = 1
	o.empty_display_type = "PLAIN_AXES"
	
	set_active(o)
	
	return o

def set_active(obj):
	"""
	Set an object as the only active, selected object
	"""
	
	# Unselect all objects
	for o in bpy.data.objects:
		o.select_set(False)
	
	# Set selected
	obj.select_set(True)
	
	# Set active
	bpy.context.view_layer.objects.active = obj

def show_message(title = "Info", message = "", icon = "INFO"):
	"""
	Show a message as a popup
	"""
	
	def draw(self, context):
		self.layout.label(text = message)
	
	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
