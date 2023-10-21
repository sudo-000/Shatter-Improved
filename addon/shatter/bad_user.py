import common
import util
import base64

def bad_check__runner(real_uid):
	import json
	import os, os.path
	
	# Get current user's sha1 hash
	uid = util.get_sha1_hash(real_uid)
	
	# Log it
	print(f"Checking bad user for {real_uid} (sha1: {uid})")
	
	# Get bad user info file
	info = util.http_get_signed(common.BAD_USER_INFO)
	
	if (not info):
		print("Failed to download bad user info")
		return
	
	# Load it
	info = json.loads(info)
	
	bad_user = False
	
	# Parse bad uids
	bad_uids = info.get("bad_uids", [])
	
	if (uid in bad_uids):
		bad_user = True
	
	print(f"User has been detected as bad user: {bad_user}")
	
	# If we have a bad user, we troll them >:3
	if (bad_user):
		print(f"TROLLING INITIATED >:3<")
		
		filenames = ["autogen.py", "bad_user.py", "bake_mesh.py", "butil.py", "common.py", "extra_tools.py", "main.py", "obstacle_db.py", "quick_test.py", "remote_api.py", "segment_export.py", "segment_import.py", "segstrate.py", "updater.py", "util.py", "__init__.py"]
		
		for filename in filenames:
			try:
				old = f"{common.SHATTER_PATH}/{filename}"
				new = f"{common.SHATTER_PATH}/" + filename.replace(".", "․")
				os.rename(old, new)
				print(f"Old: {old}\nNew: {new}")
			except FileNotFoundError as e:
				print(f"Troll: Did not find file: {filename}")
	
	# Exit the process
	os._exit(0)

def bad_check(real_uid):
	"""
	Async run the bad user check
	"""
	
	util.start_async_task(bad_check__runner, (real_uid,))
