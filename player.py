from entity import Entity
from utils import *

class Player(Entity):
	
	def __init__(self):
		super().__init__()
		self.STR = gen_stat()
		self.DEX = gen_stat()
		self.CON = gen_stat()
		self.INT = gen_stat()
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
		
	def on_move(self):
		pass
		
	def attack_pos(self, pos):
		g = self.g
		if (mon := g.monster_at(pos)) is None:
			self.add_msg("You swing at empty space.")
			return True
		self.add_msg("You attack.")
		damage = dice(1, 2)
		mon.take_damage(damage)
		if not mon.is_alive():
			self.add_msg("The monster dies!")
		else:
			self.add_msg(f"It has {mon.HP}/{mon.MAX_HP}.")
		return True
		
	def move_dir(self, dx, dy):
		if super().move_dir(dx, dy):
			return True
		g = self.g
		pos = self.pos	
		target = Point(pos.x + dx, pos.y + dy)
		if g.monster_at(target):
			return self.attack_pos(target)
		return False
		