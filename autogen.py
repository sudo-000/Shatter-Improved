"""
Automatic box details generation
"""

import math
from random import Random

class Vector3:
	def __init__(self, x = 0.0, y = 0.0, z = 0.0):
		self.x = x
		self.y = y
		self.z = z
	
	def __add__(self, other):
		return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
	
	def __sub__(self, other):
		return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
	
	def __mul__(self, other):
		return Vector3(self.x * other, self.y * other, self.z * other)

class Box:
	"""
	Very basic box info
	"""
	
	def __init__(self, pos, size):
		self.pos = pos
		self.size = size
	
	def getTop(self):
		"""
		Get top centre of the box
		"""
		
		return Vector3(self.pos.x, self.pos.y + self.size.y, self.pos.z)
	
	def getWidth(self):
		"""
		Get the width of the box
		"""
		
		return 2.0 * self.size.x
	
	def getLeftPos(self):
		"""
		Get the left plane position of the 
		"""
		
		return self.pos.x - self.size.x
	
	def placeOnTopOf(self, box):
		"""
		The the position for another place a box on top of this
		"""
		
		self.pos = box.getTop() + Vector3(y = self.size.y)
	
	def countFittingForWidth(self, width):
		"""
		Count the number of boxes that will fit left to right using the given
		(half-)width
		"""
		
		return math.ceil(self.size.x / width)

class BasicSingleRow:
	"""
	A simple single row generator algorithm for things that are actually random
	"""
	
	def __init__(self, placer, params):
		self.placer = placer
		self.base = placer.getBase()
		self.random = Random(params["seed"])
		self.width = params["size"][0] / 2
		self.depth = params["size"][1] / 2
		self.maxheight = params["max_height"]
		self.params = params
		
		self.current = self.base.countFittingForWidth(self.width)
	
	def getFirstBoxLeft(self):
		"""
		Get the first box's X pos
		"""
		
		return self.base.getLeftPos() + self.width
	
	def getOffsetFromLeftmostPosToCurrentPos(self):
		return ((self.current - 1) * (2 * self.width))
	
	def getNextHeight(self):
		return (self.random.random() / 2) * self.maxheight
	
	def next(self):
		"""
		Get the next box in the seqence
		"""
		
		# Create the base box
		b = Box(
			Vector3(0, 0, 0),
			Vector3(
				self.width,
				self.getNextHeight(),
				self.depth
			)
		)
		
		# Place it on the top centre of the other box
		b.placeOnTopOf(self.base)
		
		# Find where it needs to go along the width
		# This is starting at the left and finding which box this should be
		# based on what is set as the current box
		b.pos.x = self.getFirstBoxLeft() + self.getOffsetFromLeftmostPosToCurrentPos()
		
		# Add the box to the scene
		self.placer.addBox(b)
		
		# The next box
		self.current -= 1
	
	def hasMore(self):
		return self.current != 0

class SingleRow_ActualRandom(BasicSingleRow):
	pass

class GeometricProgressionSet(BasicSingleRow):
	"""
	Yes, this is a hack. No, I dont care. UwU
	"""
	
	def getNextHeight(self):
		return self.maxheight * self.params["geometric_ratio"] ** self.random.choice(
			[x for x in range(self.params["geometric_exponent_minmax"][0], self.params["geometric_exponent_minmax"][1])]
		)

AUTOGEN_GENERATORS = {
	"SingleRow": {
		"ActualRandom": SingleRow_ActualRandom,
		"GeometricProgressionSet": GeometricProgressionSet,
	}
}

def generate(placer, params):
	"""
	Generate decorations with the given parameters
	"""
	
	print("Yip! Autogen:", params["type"], params["algorithm"])
	
	gen = (AUTOGEN_GENERATORS[params["type"]][params["algorithm"]])(placer, params)
	
	while (gen.hasMore()):
		gen.next()
