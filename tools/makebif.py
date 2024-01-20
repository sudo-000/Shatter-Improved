"""
Make a BIF file
"""

import xml.etree.ElementTree as et
import pathlib
import gzip
import struct
import os
import sys
import util

def parse_arr(s, t = float):
	return [t(x) for x in s.split()]

def make_bif(input_file, output_file, templates, is_menu = False):
	content = None
	
	# Read in the file
	if (input_file.endswith(".gz") or input_file.endswith(".gz.mp3")):
		with gzip.open(input_file, "r") as f:
			content = f.read()
	else:
		with open(input_file, "rb") as f:
			content = f.read()
	
	# Solve templates
	if (templates):
		content = util.solve_templates(content, util.load_templates(templates))
	
	# Write bif
	seg = et.fromstring(content)
	f = open(output_file, "wb")
	
	def wf(d):
		f.write(struct.pack(f"<{len(d)}f", *d))
	
	def wi(d):
		f.write(struct.pack(f"<{len(d)}I", *d))
	
	def wb(d):
		f.write(struct.pack(f"{len(d)}B", *d))
	
	f.write(b"bif0")
	f.write(b"\x01\x00\x00\x00" if is_menu else b"\x00\x00\x00\x00")
	f.write(struct.pack("<f", float(seg.attrib.get("lightLeft", "1"))))
	f.write(struct.pack("<f", float(seg.attrib.get("lightRight", "1"))))
	f.write(struct.pack("<f", float(seg.attrib.get("lightTop", "1"))))
	f.write(struct.pack("<f", float(seg.attrib.get("lightBottom", "1"))))
	f.write(struct.pack("<f", float(seg.attrib.get("lightFront", "1"))))
	f.write(struct.pack("<f", float(seg.attrib.get("lightBack", "1"))))
	
	boxes = []
	
	for e in seg:
		if (e.tag == "box"):
			boxes.append({
				"pos": parse_arr(e.attrib.get("pos", "0 0 0")),
				"size": parse_arr(e.attrib.get("size", "1 1 1")),
				"color": parse_arr(e.attrib.get("color", "1 1 1")),
				"tileSize": parse_arr(e.attrib.get("tileSize", "0")),
				"tileRot": parse_arr(e.attrib.get("tileRot", "0"), int),
				"tile": parse_arr(e.attrib.get("tile", "0"), int),
				"visible": [int(e.attrib.get("visible", "1"))],
			})
			
			if (len(boxes[-1]["color"]) != 9):
				boxes[-1]["color"] = [
					boxes[-1]["color"][0],
					boxes[-1]["color"][1],
					boxes[-1]["color"][2],
					boxes[-1]["color"][0],
					boxes[-1]["color"][1],
					boxes[-1]["color"][2],
					boxes[-1]["color"][0],
					boxes[-1]["color"][1],
					boxes[-1]["color"][2],
				]
			
			for x in ["tile", "tileSize", "tileRot"]:
				if (len(boxes[-1][x]) != 3):
					boxes[-1][x] = [
						boxes[-1][x][0],
						boxes[-1][x][0],
						boxes[-1][x][0],
					]
	
	wi([len(boxes)])
	
	for b in boxes:
		# wi([0xdeadbeef])
		wf(b["pos"])
		wf(b["size"])
		wf(b["color"])
		wf(b["tileSize"])
		wi(b["tileRot"])
		wi(b["tile"])
		wb(b["visible"])
		wb([0])
	
	f.close()

def main():
	if (len(sys.argv) < 3):
		print(f"Usage:\n{sys.argv[0]} <input> <output> <templates>")
		return
	
	make_bif(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) >=4 else None)

if (__name__ == "__main__"):
	main()
