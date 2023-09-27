"""
Make a room, level file, append to game.xml
"""

import xml.etree.ElementTree as et
import util

class Room:
	"""
	A very basic smash hit room
	"""
	
	def __init__(self):
		self.length = 100
		self.fog = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
		self.music = "0"
		self.gravity = 1.0
		self.segments = []
		self.start = None
		self.end = None
		self.level = ""
		self.name = ""
	
	def setLevel(self, level):
		self.level = level
		return self
	
	def setName(self, name):
		self.name = name
		return self
	
	def setFog(self, bottom, top):
		self.fog[0] = bottom[0]
		self.fog[1] = bottom[1]
		self.fog[2] = bottom[2]
		self.fog[3] = top[0]
		self.fog[4] = top[1]
		self.fog[5] = top[2]
	
	def setLength(self, length):
		self.length = length
		return self
	
	def setMusic(self, music):
		self.music = music
		return self
	
	def setGravity(self, grav):
		self.gravity = grav
		return self
	
	def addSegment(self, named):
		"""
		Add a segment if it does not yet exist
		"""
		
		if (named not in self.segments):
			self.segments.append(named)
		
		return self
	
	def getCode(self):
		"""
		Get the lua for the room
		"""
		
		room = f"""function init()
	pStart = mgGetBool("start", true)
	pEnd = mgGetBool("end", true)
	
	mgMusic("{self.music}")
	mgFogColor({self.fog[0]}, {self.fog[1]}, {self.fog[2]}, {self.fog[3]}, {self.fog[4]}, {self.fog[5]})
	
"""
		
		for s in self.segments:
			room += f"""	confSegment("{self.level}/{self.name}/{s}", 1)\n"""
		
		room += f"""
	l = 0
	
	if pStart then
""" #  #
		
		if (self.start):
			room += f"""		l = l + mgSegment("{self.level}/{self.name}/{self.start}", -l)\n"""
		
		room += f"""	end
	
	local targetLen = {self.length} 
	while l < targetLen do
		s = nextSegment()
		l = l + mgSegment(s, -l)
	end
	
	if pEnd then
""" #  #
		
		if (self.end):
			room += f"""		l = l + mgSegment("{self.level}/{self.name}/{self.end}", -l)\n"""
		
		room += f"""	end
	
	mgLength(l)
end

function tick()
end
"""
		
		return room
	
	def getXML(self):
		"""
		Get the XML for the room
		"""
		
		room = et.Element('room')
		room.text = ("\n\t" if len(self.segments) > 0 else "\n")
		
		room.attrib["length"] = str(self.length)
		room.attrib["fog"] = " ".join([str(x) for x in self.fog])
		room.attrib["music"] = self.music
		room.attrib["gravity"] = str(self.gravity)
		room.attrib["overwrite-check"] = util.get_sha1_hash(self.getCode())
		
		if (self.start): room.attrib["start"] = self.start
		if (self.end): room.attrib["end"] = self.end
		
		j = 0
		for segname in self.segments:
			j += 1
			
			seg = et.SubElement(room, "segment")
			seg.attrib["name"] = segname
			seg.tail = ("\n" if len(self.segments) == j else "\n\t")
		
		return et.tostring(room).decode()
	
	def fromRoomXML(self, data):
		room = et.fromstring(data)
		
		

def appendToLevelXML(data, roomToAdd):
	"""
	Append a new room to a level xml if it doesn't yet exist
	"""
	
	level = et.fromstring(data)
	
	if (level.tag == "level"):
		already_exists = False
		
		# Check if the room is already here
		for sub in level:
			if (sub.get("type") == roomToAdd):
				already_exists = True
		
		# If not we create it
		if (not already_exists):
			# Fix spacing on the old last element
			level[-1].tail = "\n\t"
			
			# Create the element
			e = et.Element("room")
			e.set("type", roomToAdd)
			e.set("length", "300")
			e.tail = "\n"
			level.append(e)
	
	return et.tostring(level).decode()

def createLevelXML(firstRoom):
	"""
	Create an inital level XML data
	"""
	
	level = et.Element("level")
	level.text = "\n\t"
	room = et.SubElement(level, "room")
	room.set("type", firstRoom)
	room.set("length", "300")
	room.tail = "\n"
	
	return et.tostring(level).decode()

def ensureRoomInXML(path, room):
	"""
	Ensure that the `room` is in the level xml at `path`
	"""

def appendToGameXML(path, levelToAdd):
	"""
	Append a new level to the start of game.xml
	"""
	
	# Load game.xml data
	data = util.get_file(path)
	game = et.fromstring(data)
	
	# If this is a real game.xml then we will have this tag
	if (game.tag == "game"):
		levels = game[0]
		
		if (levels.tag == "levels"):
			already_exists = False
			
			# Check if it's already here
			for sub in levels:
				if (sub.get("name") == levelToAdd):
					already_exists = True
			
			# If not we add it to the start
			if (not already_exists):
				e = et.Element("level")
				e.set("name", levelToAdd)
				e.tail = "\n\t\t"
				levels.insert(0, e)
	
	# Save the game.xml data
	util.set_file(path, et.tostring(game).decode())







if __name__ == "__main__":
	# Test room class
	r = Room()
	r.setLevel("diffie").setName("hellman")
	r.setLength(140)
	r.setMusic("33")
	r.setFog([0.51, 0.61, 0.33], [0.11, 0.53, 0.72])
	r.addSegment("kex")
	r.addSegment("rsa")
	r.addSegment("eliptic")
	r.addSegment("other")
	r.addSegment("other")
	r.addSegment("other")
	print(r.getCode())
	print("=" * 80)
	print(r.getXML())
	
	# Test appending to the start of game xml
	print("=" * 80)
# 	print(appendToGameXML("""<game>
# 	<levels>
# 		<level name="basic"/>
# 		<level name="night"/>
# 		<level name="holodeck"/>
# 		<level name="endless"/>
# 		<level name="endless"/>
# 		<level name="endless"/>
# 	</levels>
# </game>""", "test"))
	
	# Test appending to the level xml
	print("=" * 80)
	print(appendToLevelXML("""<level>
	<room type="brownie/part1" length="250" start="true" end="true"/>
	<room type="brownie/part2" length="250" start="true" end="false"/>
	<room type="brownie/part2" length="250" start="false" end="true"/>
	<room type="brownie/part3" length="250" start="true" end="true"/>
	<room type="brownie/boss" length="100"/>
</level>""", "myroom/mysegment"))
	
	# Test initial room XML creation
	print("=" * 80)
	print(createLevelXML("myroom/mysegment"))