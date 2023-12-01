"""
Abstraction for segment saving and loading
"""

class BuilderType():
	"""
	Type with to/from conversion functions
	"""
	
	def __init__(self, toType = int, fromType = str):
		self.toType = toType
		self.fromType = fromType

def stringify_list(lst):
	return " ".join([str(x) for x in lst])

def listify_string(string, kind = int, require = 3, default_value = 0):
	"""
	Convert a string to a list with values of type `kind` where are at least
	`require` values. If there are not enough values from the string, the
	default value is used. If there are too many values in the string, they are
	removed.
	"""
	
	lst = [kind(x) for x in string.split()]
	
	# Append any missing values
	if (len(lst) < (require if type(require) != list else require[0] * require[1])):
		lst += [default_value for i in range(len(lst), require)]
	
	# Split list types
	if (type(require) == list):
		reallst = []
		
		for i in range(require[1]):
			reallst.append(lst[require[0] * i:require[0] * (i + 1)])
		
		lst = reallst
	elif (len(lst) > require):
		lst = lst[:require]
	
	return lst

Integer = BuilderType(int, str)
Float = BuilderType(float, str)
Point = BuilderType(lambda x: listify_string(x, float, 3, 0.0), stringify_list)
PointOverload = BuilderType(lambda x: listify_string(x, float, 3, 0.0) if len(x.split()) > 3 else listify_string(x, float, [3, 3], 0.0), stringify_list)
OverloadID = BuilderType(lambda x: listify_string(x, float, 3, 0.0), stringify_list)

FORMAT = {
	"segment": {
		"size"
	}
}