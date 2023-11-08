"""
New signing library
"""

class PrivateKey():
	def __init__(self):
		self.name = "default"
		self.type = "ed448"
		self.params = []

class PublicKey():
	def __init__(self):
		self.name = "default"
		self.type = "ed448"
		self.params = []

class Signature():
	def __init__(self):
		self.forKey = "default"
		self.params = []