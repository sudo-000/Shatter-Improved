import common
import os
import os.path as ospath
import pathlib
import tempfile
from multiprocessing import Process
import getpass
import math
import time
import json
import datetime
import hashlib
import requests
import rsa # TODO Don't use RSA anymore
import bpy
import gzip

def get_time():
	"""
	Get the current UNIX timestamp
	"""
	
	return math.floor(time.time())

def get_timestamp():
	"""
	Get a human-formatted, file-safe time string in UTC of the current time
	"""
	
	return datetime.datetime.utcnow().strftime("%Y-%m-%d %H%M%S")

def get_sha1_hash(data):
	"""
	Compute the SHA1 hash of a utf8 string
	"""
	
	return hashlib.sha1(data.encode('utf-8')).hexdigest()

gLocalIPAddressCache = ""

def get_local_ip():
	"""
	Get this computer's local IP address
	
	https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
	"""
	
	global gLocalIPAddressCache
	
	if (not gLocalIPAddressCache):
		import socket
		
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			gLocalIPAddressCache = s.getsockname()[0]
			s.close()
		except:
			gLocalIPAddressCache = ""
	
	return gLocalIPAddressCache

def get_trace():
	"""
	The user trace is the first two hex digits of the SHA1 hash of the user's
	username. This means there is only 256 possible values of the trace, so it's
	only really useful for confirming that some untampered segments might have
	been made by the same person, with a relatively high probability of error.
	
	It is meant so that someone can tell if some segments in a mod without a
	given creator name are by the same creator, and for tracking segments in
	general, while still trying to minimise privacy risk.
	"""
	
	username = getpass.getuser()
	
	result = get_sha1_hash(username)[:2]
	
	return result

def get_file(path):
	"""
	Get the data in a file if it exists
	"""
	
	try:
		return pathlib.Path(path).read_text()
	except FileNotFoundError as e:
		return None

def set_file(path, data):
	"""
	Put a text file with the given data at the given path
	"""
	
	pathlib.Path(path).write_text(data)

def get_file_json(path):
	"""
	Get a json file's contents
	"""
	
	return json.loads(get_file(path))

def set_file_json(path, data):
	"""
	Set the contents of a json file
	"""
	
	set_file(path, json.dumps(data))

def get_file_gzip(path):
	"""
	Read a gzipped file
	"""
	
	f = gzip.open(path, "rb")
	data = f.read().decode('utf-8')
	f.close()
	
	return data

def set_file_gzip(path, data):
	"""
	Write a gzipped file
	"""
	
	f = gzip.open(path, "wb")
	f.write(data.encode('utf-8'))
	f.close()

def prepare_folders(path):
	"""
	Make the folders for the file of the given name
	"""
	
	os.makedirs(pathlib.Path(path).parent, exist_ok = True)

def absolute_path(path):
	return os.path.abspath(path)

def list_folder(folder, full = True):
	"""
	List files in a folder. Full will make the paths the full file paths, false
	makes them relative to the folder.
	"""
	
	folder = absolute_path(folder)
	
	lst = []
	outline = []
	
	for root, dirs, files in os.walk(folder):
		root = str(root)
		
		for f in files:
			f = str(f)
			
			base_file_name = absolute_path(root + "/" + f)
			
			if (full):
				lst.append(base_file_name)
			else:
				lst.append(base_file_name[len(folder) + 1:])
		
		for d in dirs:
			outline.append(root + "/" + str(d))
	
	return lst

def find_apk():
	"""
	Find the path to an APK
	"""
	
	# Search for templates.xml (how we find the APK) and set path
	path = ""
	
	# If the user has set an override path, then just return that if it exists
	override = bpy.context.preferences.addons["blender_tools"].preferences.default_assets_path
	
	if (override and ospath.exists(override)):
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

def start_async_task(func, args):
	"""
	Start the given function in its own process, given arguments to pass to the
	function.
	"""
	
	p = Process(target = func, args = args)
	p.start()
	
	return p

def http_get_signed(url):
	"""
	Get the file at the given url and verify its signature, then return it's
	contents. Returns None if there is an error, like not found or invalid
	signature.
	
	Right now this is mostly copied from the updater downloading function and
	isn't used anywhere, but in the future it will replace any place where we
	need to download signed files.
	
	The key should be the same as the one used for updates.
	
	TODO Actually use this
	TODO Look into something that isn't RSA in 2023
	"""
	
	# Download data and signature
	data = requests.get(url)
	signature = requests.get(url + ".sig")
	
	if (data.status_code != 200 or signature.status_code != 200):
		return None
	else:
		data = data.content
		signature = signature.content
	
	# Load the public key
	public = eval(Path(common.BLENDER_TOOLS_PATH + "/shbt-public.key").read_text())
	
	# Verify the signature
	try:
		result = rsa.verify(data, signature, public)
	except:
		return None
	
	# Return the content of the file
	return data
