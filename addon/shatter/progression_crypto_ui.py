import bpy_extras.io_utils
import progression_crypto

from bpy.props import (
	StringProperty,
	EnumProperty,
)

from bpy.types import (
	Operator,
)

class ProgressionCrypto(bpy_extras.io_utils.ImportHelper, Operator):
	"""
	Encrypt or decrypt a smash hit progression.xml file
	"""
	
	bl_idname = "shatter.progression_crypto"
	bl_label = "Encrypt or decrypt savefile"
	
	filename_ext = ".xml"
	
	action: EnumProperty(
		name = "Action",
		description = "Weather to encrypt or decrypt",
		items = [
			('Encrypt', "Encrypt", ""),
			('Decrypt', "Decrypt", ""),
		],
		default = "Decrypt",
	)
	
	key: StringProperty(
		name = "Key",
		description = "The key/password to encrypt with",
		default = "5m45hh1t41ght",
	)
	
	def execute(self, context):
		if (len(self.key) > 0):
			progression_crypto.crypt_file(self.filepath, self.key, self.action == "Decrypt")
		
		self.report({"INFO"}, f"The file has been succesfully {self.action.lower()}ed.")
		
		return {"FINISHED"}