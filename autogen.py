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
		# When in unique mode we need the size of the previous part
		if (not hasattr(self, "prev_part")):
			self.prev_part = None
		
		# Enumerate possible values
		possible_values = [x for x in range(self.params["geometric_exponent_minmax"][0], self.params["geometric_exponent_minmax"][1])]
		
		# If we are unique and the prev_part is defined (e.g. we're not first)
		# then we need to remove the one that's the same as the prev part
		if (self.params.get("geometric_require_unique", False) and self.prev_part):
			possible_values.remove(self.prev_part)
		
		# Choose the ratio
		ratio = self.random.choice(possible_values)
		
		# Set it as the chosen one for next time
		self.prev_part = ratio
		
		return self.maxheight * self.params["geometric_ratio"] ** ratio

class UpAndDownPath(BasicSingleRow):
	"""
	Another hack ^w^
	"""
	
	def getNextHeight(self):
		"""
		Randomly walk up or down some steps
		"""
		
		# We need to create the attr and decide base height if it does not exists
		if (not hasattr(self, "prev_part")):
			self.prev_part = self.params["udpath_start"]
		
		# Decide if we go up or down
		direction = -1 if self.random.randint(0, 1) else 1
		
		# Apply the step to the previous part
		final_value = self.prev_part + direction * self.params["udpath_step"]
		
		# If really using this step makes us too high or too low, then we fix that
		if (final_value > self.params["udpath_max"] or final_value < self.params["udpath_min"]):
			final_value = self.prev_part - direction * self.params["udpath_step"]
		
		# Record our new prev part
		self.prev_part = final_value
		
		# Preform the step
		return final_value

AUTOGEN_GENERATORS = {
	"SingleRow": {
		"ActualRandom": SingleRow_ActualRandom,
		"UpAndDownPath": UpAndDownPath,
		"GeometricProgressionSet": GeometricProgressionSet,
	}
}

def generate(placer, params):
	"""
	Generate decorations with the given parameters
	"""
	
	gen_type = params.get("type", None)
	gen_algo = params.get("algorithm", None)
	
	generator_class = AUTOGEN_GENERATORS[gen_type]
	
	if (gen_algo):
		generator_class = generator_class[gen_algo]
	
	gen = generator_class(placer, params)
	
	while (gen.hasMore()):
		gen.next()
