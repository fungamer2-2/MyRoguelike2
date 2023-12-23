from utils import *
from const import *
from activity import *
from json_obj import WeaponType
import curses

class Item:
	description = "A generic item. You shouldn't see this in-game."
	
	def __init__(self):
		self.name = "item"
		self.symbol = "?"
		self.damage_taken = 0
		
	def display_color(self):
		return 0
		
	def use(self, player):
		return ItemUseResult.NOT_USED
		
class Potion(Item):
	
	def __init__(self):
		super().__init__()
		self.symbol = "p"
		
	def display_color(self):
		return curses.color_pair(COLOR_DEEP_PINK2)
		

class HealingPotion(Potion): 
	description = "A potion with a glimmering red liquid, that restores HP when consumed."
	
	def __init__(self):
		super().__init__()
		self.name = "healing potion"
		
	def use(self, player):
		player.add_msg("You drink the healing potion.")
		player.add_msg("You begin to feel more restored.", "good")	
		player.heal(dice(4, 4) + 2)
		player.poison = max(0, player.poison - rng(0, 6))
		player.use_energy(100)
		return ItemUseResult.CONSUMED

class EnlargementPotion(Potion):
	description = "A potion that will cause whoever consumes it to grow in size, increasing their HP and damage, but reducing stealth and evasion for the duration."
	
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
		return ItemUseResult.CONSUMED

class ShrinkingPotion(Potion):
	description = "A potion that will cause whoever consumes it to shrink in size, making them more stealthy and evasive, but reducing max HP and damage for the duration."
	
	def __init__(self):
		super().__init__()
		self.name = "shrinking potion"
		
	def display_color(self):
		return curses.color_pair(COLOR_CYAN)
		
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
		return ItemUseResult.CONSUMED
		
class SpeedPotion(Potion):
	description = "A potion with a blue liquid that appears to have a slight glow. When consed, it grants a temporary speed boost."
	
	def __init__(self):
		super().__init__()
		self.name = "speed potion"
		
	def display_color(self):
		return curses.color_pair(COLOR_BLUE)
			
	def use(self, player):
		player.add_msg("You drink the speed potion.")
		if player.has_status("Hasted"):
			dur = rng(10, 40)
		else:
			dur = rng(20, 60)
		player.use_energy(100)		
		player.add_status("Hasted", dur)	
		return ItemUseResult.CONSUMED
		
class InvisibilityPotion(Potion):
	description = "A potion with a rather transparent liquid. Anyone who drinks it will become temporarily invisible, but attacking while invisible will reduce its duration."
	
	def __init__(self):
		super().__init__()
		self.name = "invisibility potion"
		
	def display_color(self):
		return curses.color_pair(COLOR_BLUE)
			
	def use(self, player):
		player.add_msg("You drink the invisibility potion.")
		if player.has_status("Invisible"):
			dur = rng(20, 40)
		else:
			dur = rng(60, 100)
		player.use_energy(100)		
		player.add_status("Invisible", dur)	
		return ItemUseResult.CONSUMED

class Weapon(Item):
	description = "A weapon that can be used in combat."
	
	def __init__(self):
		super().__init__()
		self.type = None
		self.name = "weapon"
		self.damage = Dice(0, 0, 1)
		self.dmg_type = "bludgeon"
		self.finesse = False
		self.heavy = False 
		
	def roll_damage(self):
		return self.damage.roll()
		
	def display_color(self):
		return curses.color_pair(COLOR_DODGER_BLUE2) | curses.A_REVERSE
		
	@classmethod
	def from_type(cls, typ):
		obj = cls()
		obj.type = typ
		obj.name = typ.name
		obj.heavy = typ.heavy
		obj.symbol = typ.symbol
		obj.damage = typ.base_damage
		obj.dmg_type = typ.damage_type
		obj.finesse = typ.finesse
		return obj
		
	def use(self, player):
		player.add_msg(f"You wield a {self.name}.")
		player.use_energy(100)
		player.weapon = self
		return ItemUseResult.USED
		
class NullWeapon(Weapon):
	
	def __init__(self):
		super().__init__()
		self.name = "unarmed"
		self.damage = Dice(1, 1, 0)
		
	def roll_damage(self):
		return 1 + one_in(3)
		
UNARMED = NullWeapon()

class Armor(Item):
	description = "Armor that may protect its wearer from damage."
	
	def __init__(self):
		super().__init__()
		self.type = None
		self.name = "armor"
		self.protection = 1
		self.stealth_pen = 0
		self.encumbrance = 0
		
	def display_color(self):
		return curses.color_pair(COLOR_BLUE) | curses.A_REVERSE
		
	@classmethod
	def from_type(cls, typ):
		obj = cls()
		obj.type = typ
		obj.name = typ.name
		obj.symbol = typ.symbol
		obj.protection = typ.protection
		obj.stealth_pen = typ.stealth_pen
		obj.encumbrance = typ.encumbrance
		
		return obj
		
	def use(self, player):
		dur = triangular_roll(20, 40)
		player.queue_activity(EquipArmorActivity(self, dur))
		