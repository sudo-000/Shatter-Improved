"""
Segstrate, a really simple segment anti-copying thing

This works by replacing the "box", "obstacle", "powerup", "decal" and "water" tags
with randomised strings.
"""

import xml.etree.ElementTree as et
import os
import sys
import secrets
import common
import util

class Patcher:
	"""
	A thing we can use to patch a file, in this case libsmashhit.so
	"""
	
	def __init__(self, path):
		"""
		Initialise the patching utility
		"""
		
		self.f = open(path, "rb+")
	
	def __del__(self):
		"""
		When we are done with the file
		"""
		
		self.f.close()
	
	def patch(self, location, data):
		"""
		Write some data to the file at the given location
		"""
		
		self.f.seek(location, 0)
		self.f.write(data)

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
	it won't work for more than two layers of tags.
	"""
	
	root = et.fromstring(document)
	
	# Replace the root tag
	root.tag = replacements.get(root.tag, root.tag)
	
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
		
		# Load the file
		data = util.get_file_gzip(f) if compressed else util.get_file(f)
		
		# Convert it
		data = replace_tags(data, replacements)
		
		# Save it again
		util.set_file_gzip(f, data) if compressed else util.set_file(f, data)

