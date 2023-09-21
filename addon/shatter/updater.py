"""
Shatter Updater

TODO: (Important) Move to a better cryptography library for signing
This looks better than Python-RSA imo: https://github.com/wbond/oscrypto

NOTE: Contact cddepppp256<@]gmail(.}com for sensitive security issues.
"""

import json
from pathlib import Path
from hashlib import sha3_384
from multiprocessing import Process
import traceback

import common
import util

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
	
	data = util.http_get_signed(source)
	
	if (not data): return data
	
	return json.loads(data)

def update_downloader(url):
	try:
		import shutil, pathlib, os
		
		# Download data
		data = util.http_get_signed(url)
		
		if (not data):
			print("Update failed to download or verify properly")
			os._exit(0)
		
		# Get the local file path
		path = common.TOOLS_HOME_FOLDER + "/" + url.split("/")[-1].replace("/", "").replace("\\", "")
		
		# Write the data
		pathlib.Path(path).write_bytes(data)
		
		print(f"Downloaded latest update to {path}, preparing to extract.")
		
		# Extract the files (installs update)
		shutil.unpack_archive(path, common.BLENDER_ADDONS_PATH, "zip")
		
		os._exit(0)
	except:
		print(traceback.print_exc())
		os._exit(1)

def download_and_install_update(source):
	"""
	Download and install an update
	
	NOTE: WE DON'T EVER EVER EVER EVER ENABLE THIS BY DEFAULT!!!
	"""
	
	p = Process(target = update_downloader, args = (source,))
	p.start()

# def show_message(title = "Info", message = "", icon = "INFO"):
# 	"""
# 	Show a message as a popup
# 	"""
# 	
# 	import bpy, functools
# 	
# 	def draw(self, context):
# 		self.layout.label(text = message)
# 	
# 	bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)
# 
def version_compare(current, candidate, or_eq = False):
	"""
	Return True if candidate is greater than (or, if or_eq is set, if it's equal
	to) current, otherwise return False.
	
	e.g. vcmp(current, candidate) = candidate > current
	
	NOTE This is less dumb than the older function :P
	"""
	
	min_len = min(len(current), len(candidate))
	
	for i in range(min_len):
		# If the new version is bigger at this value, we can say it's new
		if (candidate[i] > current[i]):
			return True
		# If the candidate version is less than the current, we can say it's less
		elif (candidate[i] < current[i]):
			return False
	
	# In the case that they both have the same start to the version but the
	# candidate version has more array entries, we trust the new version.
	if (len(current) < len(candidate)):
		return True
	
	return or_eq

def get_latest_version(current_version, release_channel, current_blender):
	"""
	Check the new version against the current version
	"""
	
	info = download_json(common.UPDATE_INFO)
	
	# Fake info for updater test
	if (release_channel == "updatertest"):
		info = {"updatertest": {
			"version": [9999, 99, 99],
			"blender_version": [3, 0, 0],
			"download": "https://example.invalid/file.zip",
		}}
	
	if (not info):
		print("No update info (bad signature?)")
		return None
	
	info = info.get(release_channel, None)
	
	# No info on release channel
	if (info == None):
		print("No info for release channel")
		return None
	
	new_version = info.get("version", None)
	
	# Do not prompt to update things with version set to null
	if (new_version == None):
		print("No new version was put (bad file?)")
		return None
	
	# Check if the version is actually new
	if (not version_compare(current_version, new_version)):
		print(f"Current version ({current_version}) matches or is newer than latest version ({new_version})")
		return None
	
	blender_version_requirement = info.get("blender_version", [2, 60, 0])
	
	# Check if the required blender version is too great
	if (version_compare(current_blender, blender_version_requirement, True)):
		print("Blender too old to update")
		return None
	
	# Create the update object, if we need to use it
	update = Update(release_channel, new_version, info.get("download", None))
	
	return update

def check_for_updates(current_version):
	"""
	Display a popup if there is an update.
	"""
	
	import bpy, functools
	import butil
	
	if (not bpy.context.preferences.addons["shatter"].preferences.enable_update_notifier):
		return
	
	update = get_latest_version(current_version, bpy.context.preferences.addons["shatter"].preferences.updater_channel, bpy.app.version)
	
	if (update != None):
		if (bpy.context.preferences.addons["shatter"].preferences.enable_auto_update):
			download_and_install_update(update.download)
		else:
			message = f"Shatter v{update.version[0]}.{update.version[1]}.{update.version[2]} has been released! You can download the ZIP file here: {update.download}"
			
			# HACK: Defer execution to when blender has actually loaded otherwise 
			# we make it crash!
			# TODO: Look if there is some signal or event we can catch for Blender
			# startup.
			bpy.app.timers.register(functools.partial(butil.show_message, "Shatter Update", message), first_interval = 5.0)
	else:
		print("Didn't find any updates or checker is disabled.")
