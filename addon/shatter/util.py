"""
Generic utilities
"""

import os
import pathlib
from multiprocessing import Process
import math
import time
import json
import datetime
import hashlib
import requests as requests
import rsa as rsa # TODO Don't use RSA anymore
import gzip
import shutil
import sys
import importlib.util
import secrets

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

def shake256(data, length = 16):
	"""
	Compute the SHAKE-256 hash of the given data of the given length
	"""
	
	return hashlib.shake_256(data.encode('utf-8')).digest(length)

def randpw(bits = 128):
	"""
	Generate a random password
	"""
	
	alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_+-=,.!?\"\'@#%^&*~/\\:; "
	l = math.ceil(math.log(2 ** bits, len(alpha)))
	print(f"Generate {bits} bit password using {len(alpha)} symbols in alphabet * {l} symbol in phrase")
	pw = ""
	
	for i in range(l):
		nextchar = alpha[secrets.randbelow(len(alpha))]
		pw += nextchar
	
	return pw

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

def get_file_raw(path):
	"""
	Get the data in a file if it exists
	"""
	
	try:
		return pathlib.Path(path).read_bytes()
	except FileNotFoundError as e:
		return None

def set_file_raw(path, data):
	"""
	Put a binary file with the given data at the given path
	"""
	
	pathlib.Path(path).write_bytes(data)

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

def delete_path(path):
	"""
	Delete the thing at the path
	"""
	
	try:
		shutil.rmtree(path)
	except:
		try:
			os.remove(path)
		except:
			pass

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

def start_async_task(func, args):
	"""
	Start the given function in its own process, given arguments to pass to the
	function.
	"""
	
	p = Process(target = func, args = args)
	p.start()
	
	return p

def http_get_signed(url, sigurl = None):
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
	
	import common
	
	# This is needed
	PublicKey = rsa.PublicKey
	
	# Download data and signature
	data = None
	signature = None
	
	try:
		data = requests.get(url)
		signature = requests.get(url + ".sig" if not sigurl else sigurl)
	except:
		return None
	
	if (data.status_code != 200 or signature.status_code != 200):
		return None
	else:
		data = data.content
		signature = signature.content
	
	# Load the public key
	public = eval(pathlib.Path(common.SHATTER_PATH + "/data/public.key").read_text())
	
	# Verify the signature
	try:
		result = rsa.verify(data, signature, public)
	except:
		return None
	
	# Return the content of the file
	return data

def load_module(path):
	"""
	Load and return a module from the given file path, return None if it does
	not exist
	"""
	
	if (not os.path.exists(path)):
		return None
	
	module_name = "module_" + get_sha1_hash(path)
	
	spec = importlib.util.spec_from_file_location(module_name, path)
	module = importlib.util.module_from_spec(spec)
	sys.modules[module_name] = module
	spec.loader.exec_module(module)
	
	return module
