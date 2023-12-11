from entity import Entity
from player import Player
from utils import *
from pathfinding import find_path
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
		self.type = None
		
	def is_monster(self):
		return True
		
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
		
	def use_move_energy(self):
		cost = div_rand(10000, self.get_speed())
		self.use_energy(cost)
	
	def get_name(self, capitalize=False):
		the = "The" if capitalize else "the"
		return the + " " + self.name
		
	def set_state(self, state):
		self.state = state
		
	def calc_path_to(self, pos):
		g = self.g
		board = g.get_board()
		
		is_pack = self.has_flag("PACK_TRAVEL")
		
		def passable_func(p):
			return p == pos or board.passable(p)
		
		def cost_func(p):
			cost = 1
			if (c := g.monster_at(p)):
				cost += 2
			if is_pack:
				num = 0
				for m in g.monsters_in_radius(p, 1):
					if self is not m and self.is_ally(m):
						num += 1
				cost /= num + 1
			
			return cost
		
		path = find_path(board, self.pos, pos, passable_func, cost_func)
		
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
			if pos != self.path[-1] or not self.move_to(self.path.popleft()):
				#Either target tile changed, or path is blocked; recalculate path
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
		return 4 * self.INT + 8
		
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
			
		loudness = eff_vol - distance
		if loudness <= 0:
			return
		
		duration = self.INT * loudness
		
		if self.state in ["IDLE", "TRACKING"]:
			if self.soundf < duration:
				self.state = "TRACKING_SOUND"
				self.set_target(noise.pos)
				self.soundf = duration
				
	def check_alerted(self):
		if one_in(70):
			return True
		#Player's stealth check against monster's passive perception
		g = self.g
		player = g.get_player()
		roll = player.stealth_roll()
		per_mod = (self.WIS-10)/2
		perception = 10 + per_mod
		sight = self.type.blindsight
		if sight and self.distance(player) <= sight.range:
			perception += 4
		if self.has_flag("KEEN_SMELL"):
			mod = max(1 - self.distance(player)/15, 0)
			perception += 4 * mod
		perception += self.get_skill("perception")
		
		if roll < perception:
			margin = perception - roll
			return x_in_y(1, 6 - margin)		
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
			
	def do_turn(self):
		assert self.energy > 0
		if not self.can_act():
			self.energy = 0
			return
		old = self.energy
		self.move()
		if self.energy == old:
			self.energy = 0
			
	def sees_pos(self, pos):
		if super().sees_pos(pos):
			if (sight := self.type.blindsight):
				if sight.blind_beyond and self.distance(pos) > sight.range:
					return False
			return True
		return False
		
	def sees(self, other):
		if not super().sees(other):
			return False
			
		#Blindaight bypasses invisibility
		if (sight := self.type.blindsight):
			range = sight.range
			if self.distance(other) <= range:
				return True
			elif sight.blind_beyond:
				return False
		
		#TODO: Invisibility check
		return True
		
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
		
		if not one_in(4) and self.has_flag("PACK_TRAVEL") and self.set_pack_target_pos():
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
		
		if (c := g.entity_at(target)) and c.is_player() and self.distance(target) <= 1:
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
		
		return False
		#Each member of the pack tries to move toward the average of its nearby members
		for mon in g.monsters_in_radius(self.pos, 5):
			if self is mon:
				continue
			if not self.sees(mon):
				continue
			if not self.is_ally(mon):
				pass
			if mon.state == "IDLE":
				continue	
		
			p = mon.pos
			x += p.x
			y += p.y
			num += 1
		
		if num > 0:
			x /= num
			y /= num
			target = Point(round(x), round(y))
			if self.target_pos != target:
				self.set_target(target)
				return True
		return False
		
	def take_damage(self, dam):
		super().take_damage(dam)
		if self.HP <= 0:
			self.die()
		
	def die(self):
		g = self.g
		board = g.get_board()
		self.HP = 0
		self.add_msg_if_u_see(self, f"{self.get_name(True)} dies!", "good")
		board.erase_collision_cache(self.pos)
		
	def is_aware(self):
		return self.state in ["AWARE", "TRACKING"]
		
	def alerted(self):
		g = self.g
		board = g.get_board()
		if not self.is_aware():
			if self.has_flag("PACK_TRAVEL"): #If we alert one member of the pack, alert the entire pack.
				for mon in g.monsters_in_radius(self.pos, 7):	
					if self.is_ally(mon):
						mon.set_state("AWARE")
			if self.state == "IDLE":
				self.set_state("AWARE")
				
	def move_dir(self, dx, dy):
		if super().move_dir(dx, dy):
			self.use_move_energy()
			return True
		return False
		
	def get_to_hit_bonus(self):
		g = self.g
		board = g.get_board()
		
		mod = self.to_hit
		
		size = self.type.size
		
		match size:
			case "tiny":
				mod += 2
			case "small":
				mod += 1
		
		if self.has_flag("PACK_TRAVEL"):
			allies = 0
			for p in board.points_in_radius(self.pos, 1):
				if p == self.pos:
					continue
				mon = g.entity_at(p)
				if mon and self.is_ally(mon):
					allies += 1
					if allies >= 2:
						break
			if allies > 0: #Pack tactics gives a bonus to-hit if there are allies nearby
				bonus = 2.5*allies
				mod += bonus
				
		return mod
		
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
			
	def attack_pos(self, pos):
		g = self.g
		board = g.get_board()
		if not (c := g.entity_at(pos)):
			return False
		
		assert c.is_player() #TODO: Remove when it's possible for monsters to attack other monsters
		
		mod = self.get_to_hit_bonus()
		
		roll = gauss_roll(mod)
		
		if roll >= c.calc_evasion():
			damage = self.damage.roll()
			stat = self.DEX if self.type.use_dex_melee else self.STR
			damage += div_rand(stat - 10, 2)
			damage = max(damage, 1)	
			msg_type = "bad" if c.is_player() else "neutral"
			
			monster_name = self.get_name()
			target_name = c.get_name()
			msg = self.type.attack_msg
			msg = msg.replace("<monster>", monster_name)
			msg = msg.replace("<target>", target_name)
			
			if msg.startswith(monster_name):
				msg = msg.capitalize()
			
			self.add_msg_if_u_see(self, f"{msg}.", msg_type)
			c.take_damage(damage)
			poison_typ = self.type.poison
			if poison_typ:
				amount = poison_typ.max_damage
				eff_con = random.gauss(c.CON, 2.5)
				
				eff_potency = poison_typ.potency - round((eff_con - 10)/1.3)
				eff_potency = clamp(eff_potency, 0, 20)
				if eff_potency > 0:
					amount = mult_rand_frac(amount, eff_potency, 20)
					typ = "bad" if c.is_player() else "neutral"
					dmg = rng(0, amount)
					if dmg > 0:
						c.add_msg_u_or_mons("You are poisoned!", f"{self.get_name(True)} appears to be poisoned.", typ)
						c.poison += dmg
						if poison_typ.slowing and x_in_y(dmg, dmg+3):
							c.add_status("Slowed", rng(dmg, dmg*4))
		else:			
			self.add_msg_if_u_see(self, f"{self.get_name(True)}'s attack misses {c.get_name()}.")
		
		self.use_energy(100)
		return True
		
	def perception_roll(self):
		return self.roll_wisdom() + self.get_skill("perception")
		
	def move(self):
		g = self.g
		board = g.get_board()
		player = g.get_player()
		
		match self.state:
			case "IDLE":
				self.idle()				
			case "AWARE":	
				if self.sees(player):
					self.target_entity(player)
					if self.id == "bat" and one_in(5):
						self.set_rand_target()
					
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
						self.patience += rng(0, 3)
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
				
				if self.sees(player):
					self.set_state("AWARE")
					self.alerted()
				elif self.soundf <= 0:
					self.set_state("IDLE")
				
		self.move_to_target()
		
	def display_color(self):
		color = 0
		if not self.is_aware():
			color = curses.A_REVERSE	
		return color