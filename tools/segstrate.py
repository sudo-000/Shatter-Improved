"""
Segstrate, a really simple segment anti-copying thing

This works by replacing the "box", "obstacle", "powerup", "decal" and "water" tags
with randomised strings.
"""

import xml.etree.ElementTree as et
import os
import os.path
import sys
import secrets
import common as common
import util as util
from patcher import Patcher

def random_text(count):
	"""
	Generate some random base64 text
	"""
	
	return secrets.token_urlsafe(count)[:count]

def random_replacements():
	"""
	Generate random replacement strings
	"""
	
	return {
		"segment": f"_{random_text(6)}",
		"box": f"_{random_text(6)}",
		"obstacle": f"_{random_text(14)}",
		"powerup": f"_{random_text(6)}",
		"decal": f"_{random_text(6)}",
		"water": f"_{random_text(6)}",
	}

def patch_libsmashhit(path, replacements):
	"""
	Patch a libsmashhit.so to have the strings replaced for segment protection
	"""
	
	p = Patcher(path)
	
	# Patch antitamper bullshit
	p.patch(0x47130, b"\x1f\x20\x03\xd5")
	p.patch(0x474b8, b"\x3e\xfe\xff\x17")
	p.patch(0x47464, b"\x3a\x00\x00\x14")
	p.patch(0x47744, b"\x0a\x00\x00\x14")
	p.patch(0x4779c, b"\x1f\x20\x03\xd5")
	p.patch(0x475b4, b"\xff\xfd\xff\x17")
	p.patch(0x46360, b"\x13\x00\x00\x14")
	
	# Now patch the strings we need to update
	p.patch(0x211da0, replacements["segment"].encode('utf-8')) # 7 chars
	p.patch(0x211da8, replacements["box"].encode('utf-8')) # 7 chars
	p.patch(0x211db0, replacements["obstacle"].encode('utf-8')) # 15 chars
	p.patch(0x1f46c0, replacements["powerup"].encode('utf-8')) # 7 chars
	p.patch(0x211dc8, replacements["decal"].encode('utf-8')) # 7 chars
	p.patch(0x211840, replacements["water"].encode('utf-8')) # 7 chars

def replace_tags(document, replacements):
	"""
	Replace standard xml tags with the preferred ones. This is not recursive and
	it won't work for more than two layers of tags. This will also set the
	appropriate drm flags.
	"""
	
	root = et.fromstring(document)
	
	# Replace the root tag
	root.tag = replacements.get(root.tag, root.tag)
	
	# Add DRM tag
	drm = root.attrib.get("drm", "").split(" ")
	if (drm[0] == ""): drm = [] # fix stupid things
	drm.append("Segstrate")
	root.attrib["drm"] = " ".join(drm)
	
	# Replace each tag of the subnodes
	for element in root:
		element.tag = replacements.get(element.tag, element.tag)
	
	# Return the replaced stuff
	return et.tostring(root, encoding = "unicode")

def convert_folder(path, replacements):
	"""
	Recursively convert a folder to use the replacement scheme.
	"""
	
	files = util.list_folder(path)
	
	for f in files:
		compressed = None
		
		# Determine type (uncompressed, compressed, or not a segment)
		if (f.endswith(".xml.mp3")):
			compressed = False
		elif (f.endswith(".xml.gz.mp3")):
			compressed = True
		else:
			continue
		
		print(f"Converting segment: {f} (compressed = {compressed})")
		
		# Load the file
		data = util.get_file_gzip(f) if compressed else util.get_file(f)
		
		print(f"Content:\n\n{data}")
		
		# Convert it
		data = replace_tags(data, replacements)
		
		# Save it again
		util.set_file_gzip(f, data) if compressed else util.set_file(f, data)

def setup_apk(path, write_slk = True):
	"""
	Set up an apk given the path to it.
	
	Note: Using util.find_apk you need to do:
	
	util.absolute_path(f"{util.find_apk()}/../")
	
	because we need the real absolute path.
	"""
	
	libsmashhit_path = f"{path}/lib/arm64-v8a/libsmashhit.so"
	slk_path = f"{path}/assets/shatter.slk"
	segments_folder = f"{path}/assets/segments"
	
	# If segstrate already seems enabled then we throw an error
	if (os.path.exists(slk_path)):
		raise Exception("It seems like segstrate is already set up for this APK.")
	
	# Generate the segment lock file
	slk = random_replacements()
	
	# Write the segstrate info, if we need to
	if (write_slk):
		util.set_file_json(slk_path, slk)
	
	# Patch libsmashhit.so
	patch_libsmashhit(libsmashhit_path, slk)
	
	# Convert existing segments
	convert_folder(segments_folder, slk)
