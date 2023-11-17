import bpy
import bpy_extras.io_utils
import os
import butil
import patcher

from bpy.props import (
	StringProperty,
	BoolProperty,
	IntProperty,
	IntVectorProperty,
	FloatProperty,
	FloatVectorProperty,
	EnumProperty,
	PointerProperty,
)

from bpy.types import (
	Panel,
	Menu,
	Operator,
	PropertyGroup,
	AddonPreferences,
)

class PatchLibsmashhit(bpy_extras.io_utils.ImportHelper, Operator):
	"""
	Patch a libsmashhit.so file (android game binary) with some common fixes and
	tweaks.
	"""
	
	bl_idname = "shatter.patch_libsmashhit"
	bl_label = "Patch libsmashhit.so"
	
	filename_ext = ".so"
	
	do_antitamper: BoolProperty(
		name = "Disable antitamper detection",
		description = "Disables anti-tamper detection to allow modified libsmashhit.so's to run. This is required for the patch tool to work",
		default = True,
	)
	
	do_premium: BoolProperty(
		name = "Pirate premium",
		description = "Legal disclaimer: You should not use this in an APK that you distribute as that is piracy. This option only exists since it's hard to have a side-by-side version of a mod with premium legitimately enabled. Please buy the game and support the developers <3",
		default = False,
	)
	
	do_encryption: BoolProperty(
		name = "Disable save encryption",
		description = "Disable save file encryption",
		default = False,
	)
	
	do_lualib: BoolProperty(
		name = "Reenable io, os, package modules",
		description = "Reenables the io, os and package modules",
		default = False,
	)
	
	do_balls: BoolProperty(
		name = "Change starting ball count",
		description = "",
		default = False,
	)
	
	balls: IntProperty(
		name = "Balls",
		description = "",
		default = 25,
	)
	
	do_smashhitlabads: BoolProperty(
		name = "SHL mod services: ads",
		description = "Enables the use of SHL mod services adverts",
		default = False,
	)
	
	smashhitlabads: StringProperty(
		name = "Services ID",
		description = "",
		default = "",
	)
	
	do_savekey: BoolProperty(
		name = "Change save key",
		description = "Change the encryption key used with save files. Make you you've not also disabled them",
		default = False,
	)
	
	savekey: StringProperty(
		name = "Key",
		description = "",
		default = "",
	)
	
	do_fov: BoolProperty(
		name = "Change FoV",
		description = "Change the feild of view for all cameras in smash hit",
		default = False,
	)
	
	fov: FloatProperty(
		name = "Angle (degrees)",
		description = "",
		default = 60.0,
	)
	
	do_dropballs: BoolProperty(
		name = "Change dropped balls",
		description = "Allows you to change how many balls are dropped when the player is hit with an obstacle. Please remember to use this wisely and feel free to make any joke you want about the name of this tickbox OwO",
		default = False,
	)
	
	dropballs: IntProperty(
		name = "Balls",
		description = "",
		default = 10,
	)
	
	do_roomtime: BoolProperty(
		name = "Change room time",
		description = "Change the amount of time spent in each room, in seconds",
		default = False,
	)
	
	roomtime: FloatProperty(
		name = "Time (seconds)",
		description = "",
		default = 32.0,
	)
	
	do_trainingballs: BoolProperty(
		name = "Unlimit training balls",
		description = "Remove the limit of 500 balls in training mode",
		default = False,
	)
	
	do_mglength: BoolProperty(
		name = "Respect mgLength in mutliplayer",
		description = "Normally all rooms in mutliplayer have distance 200, this unlocks that and uses the given mgLength-given value instead",
		default = False,
	)
	
	do_vertical: BoolProperty(
		name = "Allow portrait mode",
		description = "Allows running the game in vertical-tall resolutions like the Shorts mod",
		default = False,
	)
	
	do_noclip: BoolProperty(
		name = "Enable no clip",
		description = "Allows the player to avoid getting hit by obstacles",
		default = False,
	)
	
	def draw(self, context):
		ui = butil.UIDrawingHelper(context, self.layout, self)
		
		ui.prop("do_antitamper", disabled = True)
		ui.prop("do_premium")
		ui.prop("do_encryption")
		ui.prop("do_lualib")
		if (ui.prop("do_balls")): ui.prop("balls")
		if (ui.prop("do_smashhitlabads")): ui.prop("smashhitlabads")
		if (ui.prop("do_savekey")): ui.prop("savekey")
		if (ui.prop("do_fov")): ui.prop("fov")
		if (ui.prop("do_dropballs")): ui.prop("dropballs")
		if (ui.prop("do_roomtime")): ui.prop("roomtime")
		ui.prop("do_trainingballs")
		ui.prop("do_mglength")
		ui.prop("do_vertical")
		ui.prop("do_noclip")
	
	def execute(self, context):
		patches = {"antitamper": None}
		
		if (self.do_premium):
			patches["premium"] = []
		
		if (self.do_encryption):
			patches["encryption"] = []
		
		if (self.do_lualib):
			patches["lualib"] = []
		
		if (self.do_balls):
			patches["balls"] = [self.balls]
		
		if (self.do_smashhitlabads):
			patches["smashhitlabads"] = [self.smashhitlabads]
		
		if (self.do_savekey):
			patches["savekey"] = [self.savekey]
		
		if (self.do_vertical):
			patches["vertical"] = []
		
		if (self.do_fov):
			patches["fov"] = [self.fov]
		
		if (self.do_dropballs):
			patches["dropballs"] = [self.dropballs]
		
		if (self.do_roomtime):
			patches["roomtime"] = [self.roomtime]
		
		if (self.do_trainingballs):
			patches["trainingballs"] = []
		
		if (self.do_mglength):
			patches["mglength"] = []
		
		if (self.do_noclip):
			patches["noclip"] = []
		
		result = patcher.patch_binary(self.filepath, patches)
		
		if (result == NotImplemented):
			butil.show_message("Error trying to patch", "It seems like the version or architecture of libsmashhit.so that you are trying to patch isn't yet supported by this tool.")
		elif (result):
			butil.show_message("Error while applying patches", "Some errors occured while patching:\n" + ("\n".join(result)))
		
		return {"FINISHED"}