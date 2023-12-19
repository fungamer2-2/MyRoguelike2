from utils import *
from const import *
from json_obj import WeaponType
import curses

class Item:
	description = "A generic item. You shouldn't see this in-game."
	
	def __init__(self):
		self.name = "item"
		self.symbol = "?"
		
	def display_color(self):
		return 0
		
	def use(self, player):
		return False
	
class Potion(Item):
	
	def __init__(self):
		super().__init__()
		self.symbol = "p"
		
	def display_color(self):
		return COLOR_DEEP_PINK2
		

class HealingPotion(Potion):
	description = "A potion with a glimmering red liquid."
	
	def __init__(self):
		super().__init__()
		self.name = "healing potion"
		
	def use(self, player):
		player.add_msg("You drink the healing potion.")
		player.add_msg("You begin to feel more restored.", "good")	
		player.heal(dice(4, 4) + 2)
		player.use_energy(100)
		return True

class EnlargementPotion(Potion):
	description = "A potion with a light red liquid."
	
	def __init__(self):
		super().__init__()
		self.name = "enlargement potion"
		
	def use(self, player):
		player.add_msg("You drink the enlargement potion.")
		if player.has_status("Enlarged"):
			dur = rng(50, 100)
		else:
			player.use_energy(50)
			dur = rng(150, 300)	
		
		player.remove_status("Reduced", True)
		player.add_status("Enlarged", dur)
		player.use_energy(100)
		player.recalc_max_hp()
		return True

class ShrinkingPotion(Potion):
	description = ""
	
	def __init__(self):
		super().__init__()
		self.name = "shrinking potion"
		
	def display_color(self):
		return COLOR_CYAN
		
	def use(self, player):
		player.add_msg("You drink the shrinking potion.")
		if player.has_status("Reduced"):
			dur = rng(50, 100)
		else:
			player.use_energy(50)
			dur = rng(150, 300)	
			
		player.remove_status("Enlarged", True)
		player.add_status("Reduced", dur)
		player.use_energy(100)
		player.recalc_max_hp()
		return True
		
class SpeedPotion(Potion):
	description = "A potion with a blue liquid that appears to have a slight glow."
	
	def __init__(self):
		super().__init__()
		self.name = "speed potion"
		
	def display_color(self):
		return COLOR_BLUE
			
	def use(self, player):
		player.add_msg("You drink the speed potion.")
		if player.has_status("Hasted"):
			dur = rng(10, 40)
		else:
			dur = rng(20, 60)
		player.use_energy(100)		
		player.add_status("Hasted", dur)	
		return True
		
class InvisibilityPotion(Potion):
	description = "A potion with a rather transparent liquid."
	
	def __init__(self):
		super().__init__()
		self.name = "invisibility potion"
		
	def display_color(self):
		return COLOR_BLUE
			
	def use(self, player):
		player.add_msg("You drink the invisibility potion.")
		if player.has_status("Invisible"):
			dur = rng(20, 40)
		else:
			dur = rng(60, 100)
		player.use_energy(100)		
		player.add_status("Invisible", dur)	
		return True

#TODO: Melee and ranged weapons/JSON for them

class Weapon:
	
	def __init__(self):
		super().__init__()
		self.name = "weapon"
		self.damage = Dice(0, 0, 1)
		self.dmg_type = "bludgeon"
		self.finesse = False
		
	def roll_damage(self):
		return self.damage.roll()
		
	def display_color(self):
		return COLOR_SILVER
		
	@classmethod
	def from_type(cls, typ):
		obj = cls()
		obj.name = typ.name
		obj.symbol = typ.symbol
		obj.damage = typ.base_damage
		obj.dmg_type = typ.damage_type
		obj.finesse = typ.finesse
		return obj
		
	def use(self, player):
		player.add_msg(f"You wield a {self.name}.")
		player.use_energy(100)
		player.weapon = self
		return True
		
class NullWeapon(Weapon):
	
	def __init__(self):
		super().__init__()
		self.name = "unarmed"
		self.damage = Dice(1, 1, 0)
		
	def roll_damage(self):
		return 1 + one_in(3)
		
UNARMED = NullWeapon()
	