"""
Level test server manager

Manages the level server(s) that are being run in the background.
"""

import util
from pathlib import Path
import os
import sys

class LevelServerManager():
	def __init__(self):
		self.server_type = "none"
		self.server_process = None
		self.params = tuple()
	
	def set_type(self, server_type):
		"""
		Set the server type
		
		NOTE: Server needs to be stopped first!
		"""
		
		self.server_type = server_type
	
	def set_params(self, params):
		"""
		Sets the params that will be given to the server run function.
		"""
		
		self.params = params
	
	def start(self):
		"""
		Starts the server if not already started
		"""
		
		if (not self.server_process and self.server_type != "none"):
			if (self.server_type not in SERVER_CALLBACKS):
				print(f"{self.server_type} is not a supported server type")
				return
			
			self.server_process = util.start_async_task(SERVER_CALLBACKS[self.server_type], self.params)
	
	def stop(self):
		"""
		Stop the server
		"""
		
		if (self.server_process):
			self.server_process.kill()
			self.server_process.join(3)
			self.server_process.close()
		
		self.server_process = None
	
	def restart(self):
		"""
		Restarts the server
		"""
		
		self.stop()
		self.start()


def cb_builtin():
	"""
	Run the builtin level server
	"""
	
	quick_test = util.load_module(str(Path(__file__).parent) + "/quick_test.py")
	quick_test.runServer()

def cmdescape(s):
	return '"' + s.replace('"', '\\"') + '"'

def cb_yorshex(asset_dir, level):
	"""
	Run yorshex's level server
	"""
	
	python_path = cmdescape(os.path.realpath(sys.executable))
	script_path = cmdescape(str(Path(__file__).parent) + "/asset_server.py")
	asset_dir = cmdescape(asset_dir)
	level = cmdescape(level)
	
	cmdline = f"{python_path} {script_path} {asset_dir} -l {level} -o"
	
	print(f"Running command: {cmdline}")
	
	status = os.system(cmdline)
	
	print(f"{cmdline}: got status {status}")

SERVER_CALLBACKS = {
	"none": None,
	"builtin": cb_builtin,
	"yorshex": cb_yorshex,
}



def main():
	sm = LevelServerManager()
	sm.set_type(sys.argv[1])
	sm.set_params(sys.argv[2:])
	sm.start()
	
	while (True):
		cmd = input(">>> ")
		
		if (cmd == "stop"):
			sm.stop()
		if (cmd.startswith("type")):
			sm.set_type(cmd[5:])
		if (cmd.startswith("params")):
			sm.set_params(cmd[7:].split("#"))
		if (cmd == "start"):
			sm.start()
		if (cmd == "exit"):
			break
	
	sm.stop()

if (__name__ == "__main__"):
	main()
