import json
from utils import *

def parse_dice(string):
	def invalid():
		raise ValueError("invalid dice format {string!r}")
	def check_digit(s):
		if not s.isdigit():
			invalid()
			
	string = string.strip()
	if string.isdigit():
		return (0, 0, int(string))
	if "d" not in string:
		invalid()
	p = string.partition("d")
	
	num = p[0]
	check_digit(num)
	
	num = int(num)
	right = p[2]
	if right.isdigit():
		return (num, int(right), 0)
	
	if "+" in right:
		p = right.partition("+")
	elif "-" in right:
		p = right.partition("-")
	else:
		invalid()
	sides = p[0]
	check_digit(sides)
	sides = int(sides)
	
	mod = p[2]
	check_digit(mod)
	mod = int(mod)
	
	return (num, sides, mod)
	
def _check_type(d, key, typ):
	if typ is not None:
		val = d[key]
		if isinstance(typ, (list, tuple)):
			types = list(typ)
		else:
			types = [typ]
		if float in types:
			types.append(int)
		
		if len(types) > 1:
			types = tuple(types)
		else:
			types = types[0]
		
		try:
			isinstance(val, types)
		except:
			
			raise Exception(str(types))
		if not isinstance(val, types):
			typ_obtained = type(val).__name__
			
			if len(types) == 1:
				typ_expected = typ.__name__
			else:
				typ_expected = ", ".join(t.__name__ for t in types)
				typ_expected = f"({typ_expected})"
			raise TypeError(f"JSON field {key!r} expected type {typ_expected}, but got type {typ_obtained}")
				

class JSONObject:
	
	def __init__(self):
		self._attrs = {}
			
	def __getattr__(self, key):
		if key not in self._attrs:
			raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {key!r}") 
		return self._attrs[key]
	
	def get_optional(self, d, key, default, typ=None, converter=None):	
		if key in d:
			_check_type(d, key, typ)
		val = d.get(key, default)
		if converter and key in d:
			val = converter(val)
		return val
		
	def get_required(self, d, key, typ=None, converter=None):
		if key not in d:
			raise KeyError(f"JSON object missing required key {key!r}")
		_check_type(d, key, typ)
		val = d[key]
		if converter:
			val = converter(val)
		return val
		
	def set_field(self, key, val):
		self._attrs[key] = val
		
	def load_from(self, key, typ):
		obj = typ.load(self._attrs[key])
		self._attrs[key] = obj
	
	def load_optional(self, d, key, default, typ=None, converter=None):	
		self.set_field(key, self.get_optional(d, key, default, typ, converter))
	
	def load_required(self, d, key, typ=None, converter=None):
		self._attrs[key] = self.get_required(d, key, typ, converter)
		
class Blindsight(JSONObject):
	
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "range", int)
		obj.load_optional(d, "blind_beyond", False)
		return obj


class Poison(JSONObject):
	
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "max_damage", int)
		obj.load_required(d, "potency", int)
		obj.load_optional(d, "slowing", False, bool)
		return obj


speed_names = ["tiny", "small", "medium", "large", "huge", "gargantuan"]		

class MonsterType(JSONObject):
	
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "id", str)
		obj.load_required(d, "name", str)
		obj.load_required(d, "symbol", str)
		obj.load_required(d, "STR", int)
		obj.load_required(d, "DEX", int)
		obj.load_required(d, "CON", int)
		obj.load_required(d, "INT", int)
		obj.load_required(d, "WIS", int)
		obj.load_required(d, "CHA", int)
		obj.load_required(d, "HP", int)
		obj.load_required(d, "level", int)
		obj.load_required(d, "diff", int)
		obj.load_required(d, "to_hit", int)
		obj.load_optional(d, "armor", 0, int)
		obj.load_optional(d, "speed", 100, int)
		obj.load_optional(d, "size", "medium", str)
		obj.load_optional(d, "attack_msg", "<monster> attacks <target>", str)
		obj.load_optional(d, "use_dex_melee", False, bool)
		obj.load_optional(d, "flags", [])
		obj.load_optional(d, "skills", {}, dict)
		
		dam = obj.get_optional(d, "base_damage", "0", str)
		obj.set_field("base_damage", Dice(*parse_dice(dam)))
		
		obj.load_optional(d, "blindsight", False, (bool, dict))
		
		if obj.blindsight != False:
			if type(obj.blindsight) != dict:
				raise TypeError("blindsight field must be a dict or False")
			obj.load_from("blindsight", Blindsight)
		
		obj.load_optional(d, "poison", False, (bool, dict))
		
		if obj.poison != False:
			if type(obj.poison) != dict:
				raise TypeError("poison field must be a dict or False")
			obj.load_from("poison", Poison)
			
		return obj
		
class EffectType(JSONObject):
			
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "name", str)
		obj.load_required(d, "type", str)
		obj.load_required(d, "apply_msg", str)
		obj.load_required(d, "extend_msg", str)
		obj.load_required(d, "remove_msg", str)
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
	
def load_effect_types():
	eff_types = {}
	f = open("effects.json", "r")
	data = json.load(f)
	for effect in data:
		name = effect["name"]
		if name in eff_types:
			raise ValueError(f"duplicate effect name {name!r}")
		typ = EffectType.load(effect)
		eff_types[name] = typ
	return eff_types
	
	

				

			