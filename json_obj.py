class JSONObject:
	
	def __init__(self):
		self._attrs = {}
		
	def __getattr__(self, key):
		if key not in self._attrs:
			raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {key!r}") 
		return self._attrs[key]
	
	def load_optional(self, d, key, default, converter=None):
		val = d.get(key, default)
		if converter and key in d:
			val = converter(val)
		self._attrs[key] = val
	
	def load_required(self, d, key, converter=None):
		if key not in d:
			raise KeyError(f"JSON object missing required key {key!r}")
		val = d[key]
		if converter:
			val = converter(val)
		self._attrs[key] = val
		
class MonsterType:
	
	@classmethod
	def load(cls, d):
		obj = cls()