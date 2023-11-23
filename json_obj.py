import json

class JSONObject:
	
	def __init__(self):
		self._attrs = {}
		
	def __getattr__(self, key):
		if key not in self._attrs:
			raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {key!r}") 
		return self._attrs[key]
	
	def get_optional(self, d, key, default, converter=None):
		val = d.get(key, default)
		if converter and key in d:
			val = converter(val)
		return val
		
	def get_required(self, d, key, converter=None):
		if key not in d:
			raise KeyError(f"JSON object missing required key {key!r}")
		val = d[key]
		if converter:
			val = converter(val)
		return vals
		
	def set_field(self, key, val):
		self._attrs[key] = val
		
	def load_from(self, key, typ):
		obj = typ.load(self._attrs[key])
		self._attrs[key] = obj
	
	def load_optional(self, d, key, default, converter=None):	
		self.set_field(key, self.get_optional(d, key, default, converter))
	
	def load_required(self, d, key, converter=None):
		if key not in d:
			raise KeyError(f"JSON object missing required key {key!r}")
		val = d[key]
		if converter:
			val = converter(val)
		self._attrs[key] = val
		
class Blindsight(JSONObject):
	
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "range")
		obj.load_optional(d, "blind_beyond", False)
		return obj
		
class MonsterType(JSONObject):
	
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "id")
		obj.load_required(d, "name")
		obj.load_required(d, "STR")
		obj.load_required(d, "DEX")
		obj.load_required(d, "CON")
		obj.load_required(d, "INT")
		obj.load_required(d, "WIS")
		obj.load_required(d, "HP")
		obj.load_required(d, "to_hit")
		obj.load_optional(d, "pack_travel", False)
		obj.load_optional(d, "blindsight", False)
		
		if obj.blindsight != False:
			if type(obj.blindsight) != dict:
				raise TypeError("blindsight field must be a dict or False")
			obj.load_from("blindsight", Blindsight)
			
		return obj
			
def load_monster_types():
	mon_types = {}
	f = open("monsters.json", "r")
	data = json.load(f)
	for mon in data:
		mon_id = mon["id"]
		if mon_id in mon_types:
			raise ValueError(f"duplicate monster id {mon_id!r}")
		typ = MonsterType.load(mon)
		mon_types[mon_id] = typ
	return mon_types
			