"""
Nice extra functions to have in Shatter
"""

import bake_mesh as bake_mesh
import util as util


def foreach_segment_in(path, callback):
	"""
	Run an action on the text of each segment in the given folder recusively
	"""

	files = util.list_folder(path)

	for f in files:
		compressed = None
		base_filename = ""

		# Determine type (uncompressed, compressed, or not a segment)
		if (f.endswith(".xml.mp3")):
			compressed = False
			base_filename = f[:-8]
		elif (f.endswith(".xml.gz.mp3")):
			compressed = True
			base_filename = f[:-11]
		else:
			continue

		# Load the file
		data = util.get_file_gzip(f) if compressed else util.get_file(f)

		# Print note
		print(f"Working on file '{f}' ...")

		# Convert it
		data = callback(data, base_filename, compressed)

		# Save it again, if we have any data to save
		if (data):
			util.set_file_gzip(f, data) if compressed else util.set_file(f, data)


def rebake_all(path, templates):
	"""
	Rebake all meshes in the given folder
	"""

	def callback(data, basename, compressed):
		bake_mesh.bakeMeshToFile(data, basename + ".mesh.mp3", templates)

	foreach_segment_in(path, callback)
