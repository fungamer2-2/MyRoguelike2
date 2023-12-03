from entity import Entity
from utils import *
from const import *

class Player(Entity):
	
	def __init__(self):
		super().__init__()
		self.STR = gen_stat() + 1
		self.DEX = gen_stat() + 1
		self.CON = gen_stat() + 1
		self.INT = gen_stat() + 1
		self.WIS = gen_stat() + 1
		self.MAX_HP = 10
		self.xp = 0
		self.xp_level = 1
		self.regen_tick = 0
		self.fov = set()
		self.energy_used = 0
		self.is_resting = False
		
	def interrupt(self):
		self.is_resting = False
		
	def use_energy(self, amount):
		super().use_energy(amount)
		self.energy_used += amount
		
	def is_player(self):
		return True
		
	def xp_to_next_level(self):
		amount = 100 * self.xp_level ** 1.5
		return round(amount/10)*10
		
	def gain_xp(self, amount):
		self.xp += amount
		old_level = self.xp_level
		while self.xp >= self.xp_to_next_level():
			self.xp -= self.xp_to_next_level()
			self.xp_level += 1	
		if old_level != self.xp_level:
			self.recalc_max_hp()
			
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
		
	def visible_monsters(self):
		g = self.g
		if len(g.monsters) < len(self.fov):
			for m in g.monsters:
				if self.sees(m):
					yield m
		else:
			for pos in self.fov:
				if (m := g.monster_at(pos)):
					yield m
		
	def get_name(self, capitalize=False):
		return "You" if capitalize else "you"
		
	def calc_to_hit_bonus(self, mon):
		level_bonus = (self.xp_level - 1) / 4
		stat_bonus = (self.STR - 10) / 2
		mod = level_bonus + stat_bonus
		if mon.state == "IDLE":
			mod += 5
		return mod
		
	def regen_rate(self):
		mult = self.CON / 10
		return 0.035 * mult
		
	def recalc_max_hp(self):
		level_mod = 5 * (self.xp_level - 1)
		level_mod *= self.CON / 10
		self.MAX_HP = round(10 + level_mod)
		
	def move_to(self, pos):
		if super().move_to(pos):
			self.fov.clear()
			self.calc_fov()
			return True
		return False
		
	def on_move(self, oldpos):
		g = self.g
		board = g.get_board()
		prev_adj = [mon for mon in g.monsters_in_radius(oldpos, 1)]
		
		for mon in prev_adj:
			if not mon.state == "AWARE":
				continue
			if self.distance(mon) >= 2 and mon.sees(self):
				player_roll = random.triangular(0, self.get_speed())
				monster_roll = random.triangular(0, mon.get_speed())
				if monster_roll >= player_roll and one_in(2):
					self.add_msg(f"{mon.get_name(True)} makes an opportunity attack as you move away!", "warning")
					oldenergy = mon.energy
					mon.attack_pos(self.pos)
					mon.energy = oldenergy
					
	def descend(self):
		g = self.g
		board = g.get_board()
		tile = board.get_tile(self.pos)
		if not tile.stair:
			self.add_msg("You can't go down there.")
			return False
		
		self.add_msg("You descend the stairs to the next level.")
		g.next_level()
		return True
		
	def take_damage(self, dam):
		if dam > 0:
			self.set_hp(self.HP - dam)
			self.interrupt()
			if 0 < self.HP <= self.MAX_HP // 5:
				self.add_msg(f"***LOW HP WARNING***", "bad")
			if self.HP <= 0:
				self.add_msg("You have died...", "bad")			
	
	def attack_pos(self, pos):
		g = self.g
		if (mon := g.monster_at(pos)) is None:
			self.add_msg("You swing at empty space.")
			return True
		
		sneak_attack = False
		mod = self.calc_to_hit_bonus(mon)
		if mon.state == "IDLE":
			if x_in_y(self.DEX, 30) and one_in(2):
				sneak_attack = True
		
		roll = gauss_roll(mod)
		evasion = mon.calc_evasion()
		if roll >= evasion:
			
			damage = dice(1, 6) + div_rand(self.STR - 10, 2)
			damage = max(damage, 1)	
			if sneak_attack:
				self.add_msg(f"You catch {mon.get_name()} off-guard!", "good")
				damage += dice(1, 6)
			
			self.add_msg(f"You hit {mon.get_name()} for {damage} damage.")
			
			mon.take_damage(damage)
			if mon.is_alive():
				self.add_msg(f"It has {mon.HP}/{mon.MAX_HP}.")
			else:
				self.on_defeat_monster(mon)
		else:
			self.add_msg(f"Your attack misses {mon.get_name()}.")
		
		self.use_energy(100)
		
		mon.alerted()
		return True
		
	def on_defeat_monster(self, mon):
		g = self.g
		self.add_msg(f"You have defeated yet another monster!", "good")
		xp_gain = 10 * mon.get_diff_level()**1.5
		xp_gain = round(xp_gain/10)*10
		self.gain_xp(xp_gain)
		
		if len(g.get_monsters()) <= 0:
			g.place_stairs()
			self.add_msg("The stairs proceeding downward to the next level begin to open up...")
			
	def move_dir(self, dx, dy):
		oldpos = self.pos.copy()
		if super().move_dir(dx, dy):
			self.use_energy(div_rand(10000, self.get_speed()))
			self.on_move(oldpos)	
			return True
		g = self.g
		pos = self.pos	
		target = Point(pos.x + dx, pos.y + dy)
		if g.monster_at(target):
			return self.attack_pos(target)
		return False
	
	def do_turn(self):
		subt = self.energy_used / 100
		self.energy_used = 0
		self.regen_tick += self.regen_rate() * subt
		while self.regen_tick >= 1:
			self.regen_tick -= 1
			self.heal(1)
			
		