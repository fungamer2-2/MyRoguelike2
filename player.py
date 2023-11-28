from entity import Entity
from utils import *

class Player(Entity):
	
	def __init__(self):
		super().__init__()
		self.STR = gen_stat()
		self.DEX = gen_stat()
		self.CON = gen_stat()
		self.INT = gen_stat()
		self.WIS = gen_stat()
		self.MAX_HP = 10
		self.xp = 0
		self.xp_level = 1
		self.regen_tick = 0
		self.fov = set()
		
	def is_player(self):
		return True
		
	def xp_to_next_level(self):
		amount = 100 * self.xp_level ** 1.5
		return round(amount/10)*10
		
	def gain_xp(self, amount):
		self.xp += amount
		while self.xp >= self.xp_to_next_level():
			self.xp -= self.xp_to_next_level()
			self.xp_level += 1	
		
	def calc_fov(self):
		g = self.g
		board = g.get_board()
		self.fov = board.get_fov(self.pos)
		
	def sees(self, other):
		if isinstance(other, Point):
			return other in self.fov
		if self is other:
			return True
		return other.pos in self.fov
		
	def get_name(self, capitalize=False):
		return "You" if capitalize else "you"
		
	def calc_to_hit_bonus(self):
		return (self.xp_level - 1) / 4
		
	def regen_rate(self):
		mult = self.CON / 10
		return 0.05 * mult
		
	def recalc_max_hp(self):
		level_mod = 5 * (level - 1)
		level_mod *= self.CON / 10
		self.MAX_HP = 10 + level_mod
		
	def move_to(self, pos):
		if super().move_to(pos):
			self.on_move()
			return True
		return False
		
	def on_move(self):
		self.fov.clear()
		self.calc_fov()
		
	def attack_pos(self, pos):
		g = self.g
		if (mon := g.monster_at(pos)) is None:
			self.add_msg("You swing at empty space.")
			return True
		
		sneak_attack = False
		mod = self.calc_to_hit_bonus()
		mod += (self.STR - 10) / 2
		if mon.state != "AWARE":
			mod += 5
			if x_in_y(self.DEX, 30) and one_in(2):
				sneak_attack = True
		
		roll = gauss_roll(mod)
		evasion = mon.calc_evasion()
		self.add_msg(f"To-hit: {gauss_roll_prob(mod, evasion):.2f}%")
		if roll >= evasion:
			if sneak_attack:
				self.add_msg(f"You catch {mon.get_name()} off-guard!")
			self.add_msg(f"You hit {mon.get_name()}.")
			damage = dice(1, 6) + div_rand(self.STR - 10, 2)
			damage = max(damage, 1)
			if sneak_attack:
				damage += dice(1, 6)
			mon.take_damage(damage)
			if not mon.is_alive():
				self.add_msg(f"{mon.get_name(True)} dies!")
			else:
				self.add_msg(f"It has {mon.HP}/{mon.MAX_HP}.")
		else:
			self.add_msg(f"Your attack misses {mon.get_name()}.")
		
		mon.alerted()
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
	
	def do_turn(self):
		self.regen_tick += self.regen_rate()
		while self.regen_tick >= 1:
			self.regen_tick -= 1
			self.heal(1)