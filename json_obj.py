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
	
	def __getstate__(self):
		return self._attrs.copy()
		
	def __setstate__(self, state):
		self._attrs = state
	
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
		
class MeleeAttackType(JSONObject):
	
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "name", str)
		obj.load_optional(d, "attack_cost", 100, int)
		
		obj.load_optional(d, "use_dex", False, bool)
		obj.load_optional(d, "reach", 1, int)
		obj.load_optional(d, "attack_msg", "<monster> hits <target>", str)
		obj.load_optional(d, "acid_strength", 0, int)
		dam = obj.get_required(d, "base_damage", str)
		obj.set_field("base_damage", Dice(*parse_dice(dam)))
		
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
		obj.load_optional(d, "armor", 0, int)
		obj.load_optional(d, "speed", 100, int)
		obj.load_optional(d, "size", "medium", str)
		
		obj.load_optional(d, "use_dex_melee", False, bool)
		obj.load_optional(d, "flags", [])
		obj.load_optional(d, "immune_status", [])
		obj.load_optional(d, "skills", {}, dict)
		obj.load_optional(d, "reach", 1, int)
		
		obj.load_optional(d, "blindsight_range", 0, int)
		obj.load_optional(d, "poison", False, (bool, dict))
		obj.load_optional(d, "weapon", None)
		obj.load_optional(d, "shield", False, bool)
		
		obj.load_optional(d, "attacks", [], list)
		obj.load_optional(d, "regen_per_turn", 0, int)
		
		for i, typ in enumerate(obj.attacks):
			obj.attacks[i] = MeleeAttackType.load(typ)	
		
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
		obj.load_optional(d, "mon_apply_msg", "", str)
		obj.load_optional(d, "mon_extend_msg", "", str)
		obj.load_optional(d, "mon_remove_msg", "", str)
		return obj
		
class WeaponType(JSONObject):
		
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "id", str)
		obj.load_required(d, "name", str)
		obj.load_required(d, "symbol", str),
		obj.load_required(d, "damage_type", str),
		
		ranged = obj.get_optional(d, "ranged", False, (bool, list))
		if ranged:
			pass
		else:
			obj.load_optional(d, "finesse", False, bool)
			obj.load_optional(d, "heavy", False, bool)
			obj.load_optional(d, "thrown", False, (bool, list))
		
		obj.load_optional(d, "two_handed", False, bool)
		
		dam = obj.get_required(d, "base_damage", str)
		obj.set_field("base_damage", Dice(*parse_dice(dam)))
		
		return obj
		
class ArmorType(JSONObject):
		
	@classmethod
	def load(cls, d):
		obj = cls()
		obj.load_required(d, "id", str)
		obj.load_required(d, "name", str)
		obj.load_required(d, "symbol", str),
		obj.load_required(d, "protection", int)
		obj.load_optional(d, "encumbrance", 0, int)
		obj.load_optional(d, "stealth_pen", 0, int)
		
		return obj
		
def load_types(filename, field_name, typ_obj):
	types = {}
	f = open(filename, "r")
	data = json.load(f)
	for obj in data:
		unique = obj[field_name]
		if unique in types:
			raise ValueError(f"duplicate {field_name} value {unique!r} in {filename}")
		typ = typ_obj.load(obj)
		types[unique] = typ
		
	return types
	
def load_monster_types():
	return load_types("monsters.json", "id", MonsterType)
	
def load_weapon_types():
	return load_types("weapons.json", "id", WeaponType)
	
def load_effect_types():
	return load_types("effects.json", "name", EffectType)
	
def load_armor_types():
	return load_types("armor.json", "id", ArmorType)
	
	
	

				

			