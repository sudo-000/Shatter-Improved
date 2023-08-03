import requests
import common
import time
import pathlib
import traceback
import util

TEST_TB_MODULE = (__name__ == "__main__")
SAVING_ENABLED = True

def report(message):
	"""
	If the user has not opted out of reporting, send a report.
	"""
	
	message = str(message) # ... because maybe ...
	
	# Log locally
	if (SAVING_ENABLED):
		pathlib.Path(common.TOOLS_HOME_FOLDER + f"/Error report {util.get_timestamp()}.log").write_text(message)

# Inject the custom exception handler
import sys

old_exception_hook = sys.excepthook

def shbt_exception_handler(type, value, trace):
	# Format the traceback
	tmsg = "\n".join(traceback.format_tb(trace))
	
	# Report traceback
	report(tmsg)
	
	# Call the old exception hook
	old_exception_hook(type, value, trace)

sys.excepthook = shbt_exception_handler

if (TEST_TB_MODULE):
	def a():
		raise Exception()
	
	def b():
		a()
	
	def c():
		b()
	
	c()
