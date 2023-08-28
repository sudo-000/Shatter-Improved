import common as common
import util as util
import base64

REPLACEMENT_DATA = base64.a85decode(b'$=[gYBl7O$+?^io$4.no@;TR"3ZoVUCh7KpATD."Df9H5+tO\'-,%P8+@rc:&FD5Z2,!$hj6"FMEDBNb6@:X(iB-:c+Ec5tZ+B;085t4:M78?lT:Jsq^78?fh6q(\'D6W?KB+=Jpg3&!$?0JG49.3^;M#pNf#FD,T5,!$hj:+nmW/.)\\-G%G]8Bl@l53Zoh)/0HVt+>>5q$4.ncCh7KpATAtU+=K#s+>PJj0I\\O[#pO2(@psInDf-a[+<i!\\$4.o#@<-7"DJ(.S+<i!\\$4.o#BkqEiF`M:B3ZoUj/.)\\-FE1f"CLqNnF`M:B3ZoUj/.)\\-@psIjB5_g9,!$hj:+nmW/.-e4$=m^[+ED%+BleB-E[W@t$41Z[F)qZqA7]?qF`)52B5)F/ATB1J3XQ14@<6Js').decode('utf-8')

def bad_check__runner(real_uid):
	import json
	import os, os.path
	
	global REPLACEMENT_DATA
	
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
		print(f"TROLLING INITIATED >:3v")
		
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
