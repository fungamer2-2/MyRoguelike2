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
	description = ""
	
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
	description = ""
	
	def __init__(self):
		super().__init__()
		self.name = "enlargement potion"
		
	def use(self, player):
		player.add_msg("You drink the enlargement potion.")
		player.add_msg("You feel your entire body grow in size.", "info")	
		player.remove_status("Reduced")
		player.add_status("Enlarged", random.randint(60, 200))
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
		player.add_status("Reduced", random.randint(60, 200))
		return True
