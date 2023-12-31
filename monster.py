from entity import Entity
from player import Player
from utils import *
from const import *
from items import Weapon
from collections import deque
import random, curses
from json_obj import *

class Monster(Entity):
	
	def __init__(self):
		super().__init__()
		self.id = "unknown"
		self.symbol = "m"
		self.name = "monster"
		self.target_pos = None
		self.state = "IDLE"
		self.patience = 0
		self.pursue_check = 0
		self.path = deque()
		self.to_hit = 0
		self.soundf = 0
		self.damage = Dice(0,0,0)
		self.weapon = None
		self.type = None
		self.bat_tick = 0
		self.energy = rng(-100, 100)
		
	def is_monster(self):
		return True
		
	def can_see(self):
		return self.has_flag("SEES")
		
	def reach_dist(self):
		reach = self.type.reach
		return max(reach, 1)
		
	def is_ally(self, other):
		if other.is_monster():
			return other.id == self.id
		return False
		
	@classmethod
	def from_type(cls, typ):
		m = cls()
		m.id = typ.id
		m.type = typ
		m.name = typ.name
		m.symbol = typ.symbol
		m.STR = typ.STR
		m.DEX = typ.DEX
		m.CON = typ.CON
		m.INT = typ.INT
		m.WIS = typ.WIS
		m.CHA = typ.CHA
		m.HP = m.MAX_HP = typ.HP
		m.to_hit = typ.to_hit
		m.damage = typ.base_damage
		
		g = m.g
		
		weap = typ.weapon
		if weap:
			weap = g.create_weapon(weap)
		m.weapon = weap
		return m
		
	def has_flag(self, name):
		return name in self.type.flags
		
	def get_skill(self, name):
		skills = self.type.skills
		return skills.get("name", 0)
		
	def base_speed(self):
		return self.type.speed
		
	def get_diff_level(self):
		return self.type.diff
		
	def get_name(self, capitalize=False):
		the = "The" if capitalize else "the"
		return the + " " + self.name
		
	def set_state(self, state):
		self.state = state
		
	def calc_path_to(self, pos):
		g = self.g
		board = g.get_board()
		
		def cost_func(p):
			cost = 1
			if (c := g.monster_at(p)) and not self.will_attack(c):
				cost += 2
			
			return cost
		
		path = board.get_path(self.pos, pos, cost_func)
		
		self.path.clear()
		if not path:
			return
		del path[0] #Remove start position		
		self.path.extend(path)
		
	def path_towards(self, pos):
		if self.pos == pos:
			self.path.clear()
			return True
		
		if self.path:
			can_path = pos == self.path[-1] and self.distance(self.path[0]) <= 1
			
			if not (can_path and self.move_to(self.path.popleft())):
				#Either target tile changed, path is blocked, or we're off-course; recalculate path
				self.calc_path_to(pos)
				if self.path:
					if self.move_to(self.path.popleft()):
						self.use_move_energy()
						return True
				return False
			return True
		else:
			self.calc_path_to(pos)	
			if self.path and self.move_to(self.path.popleft()):
				self.use_move_energy()
				return True	
			return False
			
	def base_pursue_duration(self):
		#How long to continue tracking after losing sight of the player
		return 5 * self.INT + 10
		
	def set_target(self, pos):
		if self.has_target():
			self.target_pos.set_to(pos)
		else:
			self.target_pos = pos.copy()
		
	def clear_target(self):
		self.target_pos = None
	
	def has_target(self):
		return self.target_pos is not None
		
	def on_hear_noise(self, noise):
		g = self.g
		player = g.get_player()
		
		distance = self.distance(noise.pos)
		eff_vol = noise.loudness 
		if self.has_flag("KEEN_HEARING"):
			eff_vol *= 2
		
		seen = self.sees_pos(noise.pos)
		in_player_fov = player.sees_pos(noise.pos)
			
		loudness = eff_vol - distance
		if loudness <= 0:
			return
		
		duration = self.INT * loudness
		
		if self.state in ["IDLE", "TRACKING"]:
			dist_to_player = noise.pos.distance(player.pos)
			if seen and in_player_fov and dist_to_player < rng(1, 10):
				self.alerted() 
			elif self.soundf < duration:
				self.state = "TRACKING_SOUND"
				self.set_target(noise.pos)
				self.soundf = duration
				
	def check_alerted(self):
		if one_in(70):
			return True
		#Player's stealth check against monster's passive perception
		g = self.g
		player = g.get_player()
		
		dist = self.distance(player)
		
		per_mod = stat_mod(self.WIS)
		perception = 10 + per_mod
		range = self.type.blindsight_range
		if dist <= range:
			perception += 5
			
		if not self.sees(player):
			#Player is invisible
			perception -= 5
			
		perception += self.get_skill("perception")
		
		stealth_roll = player.stealth_roll()
		
		if stealth_roll < perception:
			margin = perception - stealth_roll
			return x_in_y(1, min(dist, 7) - margin)	
		return False
		
	def tick(self):
		g = self.g
		player = g.get_player()
		
		if self.state == "TRACKING":
			if self.patience > 0:
				self.patience -= 1
		
		if self.poison > 0:
			amount = 1 + div_rand(self.poison, 10)
			amount = min(amount, self.poison)
			self.take_damage(amount)	
			self.poison -= amount
			if self.poison < 0:
				self.poison = 0
		elif one_in(16) and not self.has_flag("NO_REGEN"):
			self.heal(1)
			
		self.shield_blocks = 0
		self.tick_status_effects(100)
		
	def do_turn(self):
		assert self.energy > 0
		if not self.can_act():
			self.energy = 0
			return
		old = self.energy
		self.move()
		if self.energy == old:
			self.energy = 0
		
	def sees(self, other):
		if self is other:
			return True
			
		if not super().sees(other):
			return False
		
		blindsight_range = self.type.blindsight_range
			
		#Blindsight bypasses invisibility
		if self.distance(other) <= blindsight_range:
			return True
		
		g = self.g
		board = g.get_board()
		if self.can_see() and not other.is_invisible():
			return not board.field_blocks_view(self.pos, other.pos)
		else:
			return False
		
		
	def speed_mult(self):
		mult = super().speed_mult()
		if self.state == "IDLE":
			mult *= 0.75
		return mult
		
	def set_rand_target(self):
		g = self.g
		board = g.get_board()
		
		adj = board.get_adjacent_tiles(self.pos)	
		random.shuffle(adj)
		
		for pos in adj:
			if self.can_move_to(pos):
				self.set_target(pos)
				break
				
	def target_entity(self, ent):
		self.set_target(ent.pos)
			
	def idle(self):
		g = self.g
		board = g.get_board()
		
		if self.has_flag("PACK_TRAVEL") and self.set_pack_target_pos():
			return
			
		self.set_rand_target()
				
	def move_towards(self, target):
		g = self.g
		board = g.get_board()
		pos = self.pos
		
		delta = target - pos		
		dx = delta.x
		dy = delta.y
		if dx != 0:
			dx //= abs(dx)
		if dy != 0:
			dy //= abs(dy)
			
		has_los = self.sees_pos(target)
				
		d = abs(delta)			
		move_x = x_in_y(d.x, d.x + d.y) #Randomize, weighted by the x and y difference to the target
		if move_x:
			t = Point(pos.x + dx, pos.y)
		else:
			t = Point(pos.x, pos.y + dy)	
		
		maintains_los = board.has_line_of_sight(t, target)				
		
		switched = False
		if has_los and not maintains_los:
			move_x = not move_x	
			switched = True
		
		if move_x:
			#If one direction doesn't work, try the other
			#Only try the other direction if we can move without breaking LOS
			return self.move_dir(dx, 0) or (not switched and self.move_dir(0, dy))
		else:
			return self.move_dir(0, dy) or (not switched and self.move_dir(dx, 0))
	
	def will_attack(self, c):
		return c.is_player()
		
	def can_reach_attack(self, target):
		#Is attacking our target viable from our current position?
		
		dist = self.distance(target)
		if dist <= 1:
			return True
		
		reach = self.reach_dist()
		return dist <= reach and self.has_clear_path_to(target)
	
	def move_to_target(self):
		if not self.has_target():
			return
		
		g = self.g
		board = g.get_board()
		
		can_move = False
		for pos in board.get_adjacent_tiles(self.pos):
			if not board.passable(pos):
				continue
			if not g.entity_at(pos):
				can_move = True
				break
		if not can_move:
			#We can't move at all, so bail out
			return
		
		target = self.target_pos
		dist = self.distance(target)
		if (c := g.entity_at(target)) and self.will_attack(c):
			if self.can_reach_attack(target) and ((x_in_y(3, dist + 2) or one_in(3))):
				if self.attack_pos(target):
					return
				
		can_path = self.path_towards(target)
		
		#If we can't pathfind, try direct movement instead
		if not (can_path or self.move_towards(target)):
			#As a last resort, move randomly.
			self.set_rand_target()
			
	def set_pack_target_pos(self):
		g = self.g	
		x = 0
		y = 0
		num = 0
		player = g.get_player()
		
		#TODO: When friendly monsters are possible (through scrolls), allow it to consider anyone it's targeting, not just the player
		target_u = self.sees(player) and self.state == "AWARE"
		
		#Each member of the pack tries to move toward the average of its nearby members
		for mon in g.monsters_in_radius(self.pos, 5):
			if self is mon:
				continue
			if not self.sees(mon):
				continue
			if not self.is_ally(mon):
				pass
			if mon.state == "IDLE" and self.state != "IDLE":
				continue	
		
			p = mon.pos
			x += p.x
			y += p.y
			num += 1
		
		if num > 0:
			x /= num
			y /= num
			target = Point(round(x), round(y))
			dist_to_ent = self.distance(player)
			targ_dist_to_ent = target.distance(player.pos)
			if not target_u or targ_dist_to_ent < dist_to_ent:
				self.set_target(target)
				return True
		return False
		
	def take_damage(self, dam, src=None):
		super().take_damage(dam)
		if self.HP <= 0:
			self.die()
			if src and src.is_player():
				src.on_defeat_monster(self)
		elif src:
			self.on_hit(src)
	def die(self):
		g = self.g
		board = g.get_board()
		self.HP = 0
		self.use_energy(1000)
		self.add_msg_if_u_see(self, f"{self.get_name(True)} dies!", "good")
		board.erase_collision_cache(self.pos)
		if self.weapon and one_in(3):
			board.place_item_at(self.pos, self.weapon)
		
	def is_aware(self):
		return self.state in ["AWARE", "TRACKING"]
		
	def alerted(self):
		g = self.g
		player = g.get_player()
		board = g.get_board()
		if not self.is_aware():
			if self.has_flag("PACK_TRAVEL"): #If we alert one member of the pack, alert the entire pack.
				for mon in g.monsters_in_radius(self.pos, 6):	
					if self.is_ally(mon):
						mon.set_state("AWARE")
						mon.target_entity(player)
			self.set_state("AWARE")
		
			self.target_entity(player)
				
	def move_dir(self, dx, dy):
		if super().move_dir(dx, dy):
			self.use_move_energy()
			return True
		return False
		
	def base_damage_dice(self):
		damage = self.damage
		if self.weapon:
			damage = self.weapon.damage
		return damage
		
	def base_damage_roll(self):
		return self.base_damage_dice().roll()
		
	def calc_to_hit_bonus(self, c):
		g = self.g
		board = g.get_board()
		
		mod = self.to_hit
		
		size = self.type.size
		
		match size:
			case "tiny":
				mod += 2
			case "small":
				mod += 1
		
		if self.has_flag("PACK_TACTICS"):
			allies = 0
			for p in board.points_in_radius(self.pos, 1):
				if p == self.pos:
					continue
				mon = g.entity_at(p)
				if mon and self.is_ally(mon):
					allies += 1
					
			if allies > 0: #Pack tactics gives a bonus to-hit if there are allies nearby
				mod += 5
			
		return mod + super().calc_to_hit_bonus(c)
		
	def calc_evasion(self):
		ev = super().calc_evasion()
		size = self.type.size
		
		match size:
			case "large":
				ev -= 1
			case "huge":
				ev -= 2
			case "gargantuan":
				ev -= 4
		return ev
		
	def get_armor(self):
		return self.type.armor
		
	def get_hit_msg(self, c, damage):
		g = self.g
		player = g.get_player()
		
		u_see_attacker = player.sees(self)
		u_see_defender = player.sees(c)
		
		monster_name = self.get_name() if u_see_attacker else "something"
		target_name = c.get_name() if u_see_defender else "something"
			
		msg = self.type.attack_msg
		msg = msg.replace("<monster>", monster_name)
		msg = msg.replace("<target>", target_name)
			
		if msg.startswith(monster_name):
			msg = msg.capitalize()
			
		if damage <= 0:
			msg += " but deals no damage"
			
		return msg + "."
		
	def get_acid_strength(self):
		return self.type.acid_strength
			
	def attack_pos(self, pos):
		g = self.g
		board = g.get_board()
		player = g.get_player()
		if not (c := g.entity_at(pos)):
			return False
		
		att_roll = self.roll_to_hit(c)
		u_see_attacker = player.sees(self)
		u_see_defender = player.sees(c)
		print_msg = u_see_attacker or u_see_defender
		
		if att_roll >= 0:
			if c.shield and c.shield_blocks < 1 and att_roll < SHIELD_BONUS:
				if c.is_player():
					c.add_msg(f"You block {self.get_name()}'s attack.")
				c.shield_blocks += 1
			else:
				damage = self.base_damage_roll()
				stat = self.DEX if self.type.use_dex_melee else self.STR
				damage += div_rand(stat - 10, 2)
				damage = max(damage, 1)
				damage = apply_armor(damage, c.get_armor())
					
				msg_type = "bad" if (c.is_player() and damage > 0) else "neutral"
				if print_msg:
					self.add_msg_if_u_see(self, self.get_hit_msg(c, damage), msg_type)
					
				c.take_damage(damage)
				
				if damage > 0:
					if self.type.poison:
						self.inflict_poison_to(c)
					acid = self.get_acid_strength()
					if acid > 0:
						c.hit_with_acid(acid)
		elif u_see_attacker:
			defender = c.get_name() if u_see_defender else "something"
			self.add_msg_if_u_see(self, f"{self.get_name(True)}'s attack misses {defender}.")
		
		self.use_energy(100)
		return True
		
	def acid_resist(self):
		if self.has_flag("ACID_RESISTANT"):
			return 1
		return 0
	
	def inflict_poison_to(self, c):
		poison_typ = self.type.poison
		amount = poison_typ.max_damage
		eff_con = random.gauss(c.CON, 2.5)
				
		eff_potency = poison_typ.potency - round((eff_con - 10)/1.3)
		eff_potency = clamp(eff_potency, 0, 20)
		if eff_potency > 0:
			amount = mult_rand_frac(amount, eff_potency, 20)
			typ = "bad" if c.is_player() else "neutral"
			dmg = rng(0, amount)
			if dmg > 0:
				if c.is_player():
					c.do_poison(dmg)
				else:
					c.add_msg_if_u_see("You are poisoned!", f"{self.get_name(True)} is poisoned!", typ)
					c.poison += dmg
				if poison_typ.slowing and x_in_y(dmg, dmg+3):
					paralyzed = False
					if self.has_status("Slowed") and one_in(5):
						c.add_status("Paralyzed", rng(1, 5))
						paralyzed = True			
					c.add_status("Slowed", rng(dmg, dmg*4), paralyzed)
									
	def random_guess_invis(self):
		g = self.g
		board = g.get_board()
		chance = 1
		target = None
		for pos in board.points_in_radius(self.pos, 3):
			if self.sees_pos(pos) and one_in(chance):
				chance += 1
				target = pos
		if target:
			self.set_target(target)	
	
	def determine_invis(self, c):
		g = self.g
		player = g.get_player()
		
		dist = self.distance(c)
		if dist <= 1 and one_in(4):
			return True
			
		return self.perception_roll() >= player.stealth_roll()
		
	def perception_roll(self):
		return self.roll_wisdom() + self.get_skill("perception")
	
	def get_size(self):
		return self.type.size
	
	def on_hit(self, ent):
		g = self.g
		
		if self.has_flag("PACK_TRAVEL"):
			for mon in g.monsters_in_radius(self.pos, rng(8, 16)):
				if self is mon:
					continue
				if not self.is_ally(mon):
					continue
				
				if not one_in(3):
					self.set_state("AWARE")
	
	def move(self):
		g = self.g
		board = g.get_board()
		player = g.get_player()	
		
		reached_target = self.target_pos == self.pos
		is_targeting_u = self.has_target() and self.target_pos == player.pos
		
		if reached_target:
			self.clear_target()
		
		match self.state:
			case "IDLE":
				self.idle()				
			case "AWARE":	
				if self.sees(player):
					if not (self.has_flag("PACK_TRAVEL") and self.set_pack_target_pos()):
						self.target_entity(player)
						
					if self.id == "bat" and one_in(4):
						self.set_rand_target()
				elif self.sees_pos(player.pos): 
					#Target is in LOS, but invisible
					perceived_invis = self.determine_invis(player)
					
					if not is_targeting_u and reached_target:
						if perceived_invis:	
							self.target_entity(player)
						else:
							self.random_guess_invis()				
				else:
					self.set_state("TRACKING")
					self.target_entity(player)
					self.pursue_check = 0
					patience = self.base_pursue_duration()	
					self.patience = round(patience * random.triangular(0.8, 1.2))
				
			case "TRACKING":
				if self.pursue_check > 0:
					self.idle()
					self.pursue_check -= 1
					if self.pursue_check <= 0:
						self.clear_target()
				elif not self.has_target() or self.target_pos == self.pos:
					#Once we reach the target, make a perception check contested by the player's stealth check to determine the new location
					if self.perception_roll() >= player.stealth_roll():
						self.set_target(player.pos)
					elif self.has_flag("PACK_TRAVEL") and self.set_pack_target_pos():
						self.patience += rng(0, 1)
					else:
						#If we fail, idle around for a few turns instead
						self.pursue_check = rng(1, 4)
						self.idle()
						
		
				if self.sees(player):
					self.set_state("AWARE")
				elif self.patience <= 0:
					self.set_state("IDLE")
					
			case "TRACKING_SOUND":
				if self.soundf > 0:
					self.soundf -= 1
				
				stealth_val = 10 + player.stealth_mod()
				if self.sees(player) and one_in(2) and self.perception_roll() >= stealth_val:
					self.set_state("AWARE")
					self.alerted()
				elif self.soundf <= 0:
					self.set_state("IDLE")
				
		self.move_to_target()
		
	def push_away_from(self, pos, distance):
		if self.pos == pos:
			return
		
		diff = self.pos - pos
		dist = self.distance(pos)
		
		norm_x = diff.x / dist
		norm_y = diff.y / dist
		
		delta = Point(round(norm_x * distance), round(norm_y * distance))
		
		target = self.pos + delta
		
		moved = False
		for p in points_in_line(self.pos, target):
			if self.is_valid_move(self.pos, p):
				self.move_to(p)
				moved = True
			else:
				break
				
		return moved
		
	def display_color(self):
		color = 0
		if not self.is_aware():
			color = curses.A_REVERSE	
		return color