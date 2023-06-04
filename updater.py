"""
Shatter Updater

TODO: (Important) Move to a better cryptography library for signing
This looks better than Python-RSA imo: https://github.com/wbond/oscrypto

NOTE: Contact cddepppp256@gmail.com for sensitive security issues.
"""

import common
import bpy, functools
import requests
import json
import rsa
from pathlib import Path
PublicKey = rsa.PublicKey

from hashlib import sha3_384
from bpy.types import (UILayout)
from multiprocessing import Process

UPDATE_INFO = common.UPDATE_INFO
TOOLS_HOME_FOLDER = common.TOOLS_HOME_FOLDER
LEGACY_UPDATE_MESSAGES = True
BLENDER_TOOLS_PATH = common.BLENDER_TOOLS_PATH

class Update():
	"""
	Class representing an update
	
	TODO This does not need to be a class, could just be a dict
	"""
	
	def __init__(self, release_channel, version, download):
		self.release_channel = release_channel
		self.version = version
		self.download = download

def download_json(source):
	"""
	Download JSON file
	"""
	
	return json.loads(requests.get(source).content)

def download_update(source):
	"""
	Download an update
	
	For now we do not install it until I learn how software signing works under
	the hood (and until that is implemented)
	
	**NOTE** ALSO WE DON'T EVER EVER EVER EVER ENABLE THIS BY DEFAULT
	"""
	
	def update_downloader(url):
		import shutil, pathlib, os
		
		# TODO Port to using util.http_get_signed()
		# Download data and signature
		data = requests.get(url).content
		signature = requests.get(url + ".sig").content
		
		# Load the public key
		public = eval(Path(BLENDER_TOOLS_PATH + "/shbt-public.key").read_text())
		
		# Verify the signature
		try:
			result = rsa.verify(data, signature, public)
		except:
			os._exit(0)
		
		# Get the local file path
		path = TOOLS_HOME_FOLDER + "/" + url.split("/")[-1].replace("/", "").replace("\\", "")
		
		# Write the data
		pathlib.Path(path).write_bytes(data)
		
		print("Smash Hit Tools: Downloaded latest update to " + path + ", preparing to extract.")
		
		# Extract the files (installs update)
		shutil.unpack_archive(path, BLENDER_TOOLS_PATH, "zip")
		
		os._exit(0)
	
	p = Process(target = update_downloader, args = (source,))
	
	p.start()

def show_message(title = "Info", message = "", icon = "INFO"):
	"""
	Show a message as a popup
	"""
	
	if (LEGACY_UPDATE_MESSAGES):
		def draw(self, context):
			self.layout.label(text = message)
		
		bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
	else:
		bpy.ops.sh.show_message('EXEC_DEFAULT', message = message)

def check_version_lt(new_version, current_version):
	"""
	Check if new_version > current_version
	
	TODO: This is a really bad way of doing this. Make it not a really bad way
	of doing this.
	"""
	
	if (new_version[0] > current_version[0]):
		return True
	elif (new_version[0] == current_version[0]):
		if (new_version[1] > current_version[1]):
			return True
		elif (new_version[1] == current_version[1]):
			if (new_version[2] > current_version[2]):
				return True
			elif (new_version[2] == current_version[2]):
				# We used to not have four part versions
				if (len(new_version) == 3 and len(current_version) == 3):
					return False
				elif (len(new_version) < len(current_version)):
					return False
				elif (len(new_version) > len(current_version)):
					return True
				else:
					if (new_version[3] > current_version[3]):
						return True
	
	return False

def version_compare_new(current, candidate):
	"""
	Return True if candidate is greater than current, otherwise return False.
	
	NOTE This is less dumb
	TODO Switch to using this one now
	"""
	
	min_len = min(len(current), len(candidate))
	
	for i in range(min_len):
		# If the new version is bigger at this value, we can say it's new
		if (candiate[i] > current[i]):
			return True
		# If the candidate version is less than the current, we can say it's less
		elif (candiate[i] < current[i]):
			return False
	
	# In the case that they both have the same start to the version but the
	# candidate version has more array entries, we trust the new version.
	if (len(current) < len(candidate)):
		return True
	
	return False

def get_latest_version(current_version, release_channel):
	"""
	Check the new version against the current version
	"""
	
	try:
		# TODO Require signature for update info
		info = download_json(UPDATE_INFO).get(release_channel, None)
		
		# No info on release channel
		if (info == None):
			return None
		
		new_version = info["version"]
		
		# Do not prompt to update things with version set to null
		if (new_version == None):
			return None
		
		# Check if the version is actually new
		if (not check_version_lt(new_version, current_version)):
			return None
		
		blender_version_requirement = info["blender_version"]
		
		# Check if our blender version is compatible
		if (check_version_lt(blender_version_requirement, bpy.app.version)):
			return None
		
		# Create the update object, if we need to use it
		update = Update(release_channel, new_version, info["download"])
		
		return update
	
	except Exception as e:
		print(f"Smash Hit Tools: Error checking for new versions:\t\t{e}")
		
		return None

def check_for_updates(current_version):
	"""
	Display a popup if there is an update.
	"""
	
	if (not bpy.context.preferences.addons["blender_tools"].preferences.enable_update_notifier):
		return
	
	update = get_latest_version(current_version, bpy.context.preferences.addons["blender_tools"].preferences.updater_channel)
	
	if (update != None):
		message = f"Shatter for Blender {update.version[0]}.{update.version[1]}.{update.version[2]} (for {update.release_channel} branch) has been released! Download the ZIP file here: {update.download}"
		
		if (bpy.context.preferences.addons["blender_tools"].preferences.enable_auto_update):
			download_update(update.download)
			message = f"Shatter for Blender update to {update.version[0]}.{update.version[1]}.{update.version[2]} (for {update.release_channel} branch) has been installed. Please restart Blender to see changes!"
		
		# HACK: Defer execution to when blender has actually loaded otherwise 
		# we make it crash!
		# TODO: Look if there is some signal or event we can catch for Blender
		# startup.
		bpy.app.timers.register(functools.partial(show_message, "Shatter for Blender Update", message), first_interval = 5.0)
	else:
		print("Smash Hit Tools: Up to date (or checker failed or disabled)!")
