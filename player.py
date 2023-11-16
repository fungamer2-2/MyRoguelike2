from entity import Entity
from utils import gen_stat

class Player(Entity):
	
	def __init__(self):
		super().__init__()
		self.STR = gen_stat()
		self.DEX = gen_stat()
		self.CON = gen_stat()
		
		self.MAX_HP = 10
		self.level = 1
		
	def calc_to_hit_bonus(self):
		return (self.level - 1) / 3
		
	def regen_rate(self):
		mult = self.CON / 10
		return 0.05 * mult
		
	def recalc_max_hp(self):
		level_mod = 5 * (level - 1)
		level_mod *= self.CON / 10
		self.MAX_HP = 10 + level_mod
		
	