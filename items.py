from utils import *
from const import *
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
		self.symbol = "P"
		
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
		player.heal(dice(3, 4) + 3)
		player.use_energy(100)
		return True

class EnlargementPotion(Potion):
	description = "A potion with a light red liquid."
	
	def __init__(self):
		super().__init__()
		self.name = "enlargement potion"
		
	def use(self, player):
		player.add_msg("You drink the enlargement potion.")
		player.add_msg("You feel your entire body grow in size.", "info")	
		player.remove_status("Reduced")
		player.add_status("Enlarged", rng(100, 200))
		player.use_energy(150)
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
		player.add_msg("You drink the shrink potion.")
		player.add_msg("You feel your entire body shrink in size.", "info")	
		player.remove_status("Enlarged")
		player.add_status("Reduced", rng(100, 200))
		player.use_energy(150)
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
			player.add_msg("You feel that your speed lasts longer.", "info")
			dur = rng(10, 40)
		else:
			player.add_msg("You feel your movements speed up as time appears to slow down.", "good")
			dur = rng(20, 60)
		player.use_energy(100)		
		player.add_status("Hasted", dur)	
		return True

