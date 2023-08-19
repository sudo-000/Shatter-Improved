import requests
import common
import json
import util
import os, os.path
import secrets
from urllib.parse import quote

ACCOUNT_INFO_DIR = common.TOOLS_HOME_FOLDER + "/Account Information"

class WeakUserInfo:
	def __init__(self, uid, token):
		self.uid = uid
		self.token = token

def load_weak_user(uid):
	"""
	Load the weak user's UID and token from a file in the shatter folder. Note:
	If the user doesn't exist, it will (try) to create it on the server so this
	might take a long time!
	"""
	
	if (not os.path.exists(ACCOUNT_INFO_DIR)):
		os.makedirs(ACCOUNT_INFO_DIR, exist_ok = True)
	
	path = ACCOUNT_INFO_DIR + f"/{uid}.json"
	
	# Create the weak user info if it doesn't exist
	if (not os.path.exists(path)):
		# Randomly generated token/password for the account
		token = secrets.token_hex(32)
		
		# Set the user info file
		util.set_file_json(path, {
			"uid": uid,
			"token": token,
		})
		
		# Send request to make the user to remote
		weak_user_check(WeakUserInfo(uid, token))
	
	# Load user data info
	info = util.get_file_json(path)
	
	# Make the proper object for it
	return WeakUserInfo(info["uid"], info["token"])

def get_user_info(uid):
	"""
	Get user info, using `uid` if the uid has not been set
	"""
	
	pass #TODO

def encode_qs(d):
	"""
	Encode a query string
	"""
	
	s = []
	
	for k in d:
		s.append(f"{quote(k)}={quote(d[k])}")
	
	return "&".join(s)

def send_request(action, params):
	"""
	Send a request to the Shatter server
	"""
	
	result = requests.post(f"{common.SHATTER_API}{action}", data = params).text
	
	return json.loads(result)

def weak_user_check(weak):
	"""
	Check in to a weak user account (will be created if it does not exist)
	
	Since weak users don't have real sessions this actually doesn't do anything
	"""
	
	result = send_request("weak-user-check", {
		"uid": weak.uid,
		"token": weak.token,
		"magic": "13aa2d6dddaf25aa3900db0b74e10caa", # md5("theGameInIts")
	})
	
	return (result["status"] == "done")

def weak_user_claim_segment(weak, data):
	"""
	Claim a segment given the user and data
	"""
	
	result = send_request("weak-user-claim", {
		"uid": weak.uid,
		"token": weak.token,
		"magic": "9c1e3867031a5448c4738c7654e4a587", # md5("popularFurryVtuberYorshex")
		"data": data,
	})
	
	return (result["status"] == "done")

def weak_user_set_creator(weak, name):
	"""
	Claim a segment given the user and data
	"""
	
	result = send_request("weak-user-set-name", {
		"uid": weak.uid,
		"token": weak.token,
		"magic": "b749a6adb07dc0be75c9a54e86d8672d", # md5("thisApiSucks")
		"name": name,
	})
	
	return (result["status"] == "done")

def claim_segment_text(context, text):
	"""
	Try to claim the segment text as being made by the creator
	"""
	
	preferences = context.preferences.addons["blender_tools"].preferences
	
	s = weak_user_claim_segment(load_weak_user(preferences.uid), text)
	
	print(f"Weak user claim segment status: {s}")

def creator_name_updated_callback(self, context):
	"""
	Callback for when the value of creator name is changed in Shatter settings
	"""
	
	preferences = context.preferences.addons["blender_tools"].preferences
	
	s = weak_user_set_creator(load_weak_user(preferences.uid), preferences.creator)
	
	print(f"Creator name update status: {s}")
