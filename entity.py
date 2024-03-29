from utils import *
from const import *
from abc import abstractmethod, ABC
import random

class Entity(ABC):
	g = None
	
	def __init__(self):
		self.STR = 10
		self.DEX = 10
		self.CON = 10
		self.INT = 10
		self.WIS = 10
		self.CHA = 10
		self.HP = self.MAX_HP = 10
		self.pos = Point()
		self.energy = 100
		self.poison = 0
		self.status = {}
		self.shield = None
		self.shield_blocks = 0
		
	def is_valid_move(self, oldpos, newpos):
		diff = newpos - oldpos
		abs_diff = abs(diff)
		if abs_diff.x > 1 or abs_diff.y > 1:
			return False
		
		if abs_diff.x == 1 and abs_diff.y == 1:
			p1 = Point(oldpos.x + diff.x, oldpos.y)
			p2 = Point(oldpos.x, oldpos.y + diff.y)
			blocked = (not self.can_move_to(p1)) + (not self.can_move_to(p2))
			if blocked >= 2:
				return False
				
		return self.can_move_to(newpos)
		
	def roll_to_hit(self, other):
		if x_in_y(MIN_HIT_MISS_PROB, 100):
			return 1000 if one_in(2) else -1000
		
		roll = gauss_roll(self.calc_to_hit_bonus(other))
		evasion = other.calc_evasion()
		
		return roll - evasion
		
	def get_all_status_effects(self):
		for name in self.status:
			yield name
		
	def has_status(self, name):
		g = self.g
		g.check_effect_type(name)
		return name in self.status
		
	def add_status(self, name, dur):
		if not self.has_status(name):
			self.status[name] = 0
		self.status[name] += dur*100
		
	def adjust_duration(self, name, amount):
		if self.has_status(name):
			self.status[name] += amount*100
			if self.status[name] <= 0:
				self.remove_status(name)
		
	def remove_status(self, name):
		if self.has_status(name):
			del self.status[name]
			
	def is_immune_status(self, name):
		return False
		
	def use_energy(self, amount):
		self.energy -= amount
		
	def use_move_energy(self):
		cost = div_rand(10000, self.get_speed())
		self.use_energy(cost)
		
	def is_player(self):
		return False
		
	def is_monster(self):
		return False
		
	def is_invisible(self):
		return self.has_status("Invisible")
		
	def calc_evasion(self):
		dex = self.DEX
		if not self.is_alive():
			dex = 0
		return 10 + stat_mod(dex)
		
	def base_speed(self):
		return 100
	
	def get_speed(self):
		return round(self.base_speed() * self.speed_mult())
		
	def speed_mult(self):
		mult = 1
		if self.has_status("Slowed"):
			mult = 0.5
		return mult
		
	def can_act(self):
		return not self.has_status("Paralyzed")
		
	def get_armor(self):
		return 0
	
	@abstractmethod
	def get_name(self, capitalize=False):
		return "Unknown Entity"
		
	def calc_to_hit_bonus(self, other):
		mod = 0
		if not self.sees(other):
			mod -= 5
		if not other.sees(self):
			mod += 5
		return mod
	
	def on_hear_noise(self, noise):
		pass
		
	def add_msg(self, text, typ="neutral"):
		g = self.g
		g.add_message(text, typ)
		
	def add_msg_u_or_mons(self, u_msg, mon_msg, typ="neutral"):
		g = self.g
		player = g.get_player()
		if self.is_player():
			self.add_msg(u_msg, typ)
		elif self.is_monster() and player.sees(self):
			self.add_msg(mon_msg, typ)
		
	def add_msg_if_u_see(self, other, text, typ="neutral"):
		g = self.g
		player = g.get_player()
		if player.sees(other):
			self.add_msg(text, typ)
		
	def can_move_to(self, pos):
		g = self.g
		board = g.get_board()
		if pos == self.pos:
			return True
		ent_check = False
		
		if self.is_player():
			ent_check = g.monster_at(pos)
		else:
			ent_check = g.entity_at(pos)
			
		return board.passable(pos) and not ent_check
		
	def move_to(self, pos):
		board = self.g.get_board()
		if self.can_move_to(pos):
			old_pos = self.pos.copy()
			board.erase_collision_cache(old_pos)
			self.pos = pos
			board.set_collision_cache(pos, self)
			return True
		return False
		
	def move_dir(self, dx, dy):
		return self.move_to(self.pos + Point(dx, dy))
	
	def set_hp(self, HP):
		self.HP = clamp(HP, 0, self.MAX_HP)
		
	def take_damage(self, dam, src=None):
		if dam > 0:
			self.set_hp(self.HP - dam)
	
	def has_clear_path_to(self, other):
		g = self.g
		board = g.get_board()
		return board.has_clear_path(self.pos, other)
		
	def heal(self, amount):
		if amount > 0:
			self.set_hp(self.HP + amount)
	
	def is_alive(self):
		return self.HP > 0
		
	def distance(self, other):
		if isinstance(other, Point):
			return self.pos.distance(other)
		return self.pos.distance(other.pos)
		
	def sees_pos(self, pos):
		board = self.g.get_board()
		return board.has_line_of_sight(self.pos, pos)
		
	def sees(self, other):	
		if self is other: #We always see ourselves
			return True
		
		return self.sees_pos(other.pos)
			
	def has_clear_path(self, pos):
		board = self.g.get_board()
		return board.has_clear_path(self.pos, pos)		
		
	def display_color(self):
		return 0
		
	def is_aware(self):
		return True
		
	def do_turn(self):
		pass
		
	def make_noise(self, volume):
		g = self.g
		g.add_noise_event(self.pos, volume, self)	
	
	def acid_resist(self):
		#Resistance to acid
		# -1 is vulnerable, +1 is resistant, +2 is immune
		return 0
		
	def hit_with_acid(self, strength):
		res = self.acid_resist()
		if res >= 2:
			return
			
		if res < 0:
			strength *= 2
		elif res == 1:
			strength = div_rand(strength, 2)
			
		armor = self.get_armor()
		strength -= rng(0, armor)
		
		if strength <= 0:
			return
		
		dam = rng(1, strength) 
		
		severity = " terribly" if res < 0 else ""
		self.combat_msg(f"The acid burns you{severity}!", f"{self.get_name(True)} is burned{severity} by the acid!")
		self.take_damage(dam)
			
	def combat_msg(self, u_msg, mon_msg=None):
		if mon_msg is None:
			mon_msg = u_msg
		typ = "bad" if self.is_player() else "neutral"
		self.add_msg_u_or_mons(u_msg, mon_msg, typ)
	
	def dex_mod(self):
		return stat_mod(self.DEX)
		
	def wis_mod(self):
		return stat_mod(self.WIS)
				
	def stealth_mod(self):
		return self.dex_mod()
		
	def roll_wisdom(self):
		return gauss_roll(stat_mod(self.WIS))
		
	def stealth_roll(self):
		return gauss_roll(self.stealth_mod())
		
	def dex_mod(self):
		return stat_mod(self.DEX)	
	
	def get_perception(self):
		return 10 + self.wis_mod()
	
	def tick_status_effects(self, amount):
		for name in list(self.status.keys()):
			self.status[name] -= amount
			if self.status[name] <= 0:
				self.remove_status(name)
			
	def apply_resist(self, dam, typ):
		return dam
				
	def get_size(self):
		return "medium"
		
	def ranged_evasion(self):
		mod = 0
		
		match self.get_size():
			case "tiny":
				mod = +2
			case "small":
				mod = +1
			case "large":
				mod = -1
			case "huge":
				mod = -2
			case "gargantuan":
				mod = -4
		ev = 10 + self.dex_mod()
		
		if self.is_monster() and not self.is_aware():
			mod -= 5
			
		return ev + mod
		
	def apply_armor(self, dam):
		return apply_armor(dam, self.get_armor())
				
	def shoot_projectile_at(self, target_pos, proj):
		g = self.g
		board = g.get_board()
		
		target = target_pos.copy()
		acc_roll = gauss_roll(proj.accuracy)
		acc_margin = acc_roll - 5
		
		
		wild_miss = False
		if acc_margin < 0 and self.distance(target) > 1:
			#An inaccurate projectile targets a random nearby point instead
			max_fuzz = div_rand(max(0, self.distance(target) - 2), 6) + 1
			for _ in range(100):
				target = target_pos.copy()
				target.x += rng(-max_fuzz, max_fuzz)
				target.y += rng(-max_fuzz, max_fuzz)
				if target == target_pos:
					continue
				if self.sees_pos(target):
					break
			wild_miss = True
			if self.is_player():
				self.add_msg("Your aim is off, and you completely miss!")
			
		target_creature = g.entity_at(target)
		
		dist = 0
		proj.final_pos = self.pos
		for pos in g.do_projectile(self.pos, target):
			if not board.passable(pos):
				break
			dist += 1
			if dist > proj.long_range:
				break
				
			proj.final_pos = pos
			penalty = calc_ranged_penalty(dist, proj.short_range, proj.long_range)
			
			if (c := g.entity_at(pos)):
				ev = c.ranged_evasion()
				
				if target_creature and target_creature is c:
					margin = acc_roll - penalty - ev
					
					if margin >= 0:
						proj.on_hit(self, c, margin)				
						break
					else:
						if not wild_miss:
							self.add_msg_if_u_see(c, f"The {proj.name} misses {c.get_name()}.")
						if c.is_monster() and one_in(2):
							if self.is_player():
								c.alerted()	
							
				else: #We may have hit an unintended target
					unintended_hit = 15 - rng_float(0, acc_margin) - ev
					if unintended_hit >= 0:			
						proj.on_hit(self, c, 0)
						break
					elif one_in(2) and c.is_monster():
						if self.is_player():
							c.alerted()
		