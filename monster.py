from entity import Entity
from player import Player
from utils import *
from pathfinding import find_path
from collections import deque
import random
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
		self.path = deque()
		self.pack = True
		self.to_hit = 0
		self.awareness = 0
		self.damage = Dice(0,0,0)
		
	def is_monster(self):
		return True
		
	def is_ally(self, other):
		return other.id == self.id
		
		
	@classmethod
	def from_type(cls, typ):
		m = cls()
		m.id = typ.id
		m.name = typ.name
		m.STR = typ.STR
		m.DEX = typ.DEX
		m.CON = typ.CON
		m.INT = typ.INT
		m.WIS = typ.WIS
		m.HP = m.MAX_HP = typ.HP
		m.pack = typ.pack_travel
		m.to_hit = typ.to_hit
		m.damage = typ.base_damage
		return m
	
	def get_name(self, capitalize=False):
		the = "The" if capitalize else "the"
		return the + " " + self.name
		
	def calc_path_to(self, pos):
		g = self.g
		board = g.get_board()
		def passable_func(p):
			return p == pos or board.passable(p)
		cost_func = lambda p: 1
		def cost_func(p):
			return 1 + 2*(g.monster_at(p) is not None)
		
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
				self.calc_path_to(pos)
				if self.path:
					return self.move_to(self.path.popleft())
				return False
			return True
		else:
			self.calc_path_to(pos)	
			if self.path:
				return self.move_to(self.path.popleft())	
			return False
			
	def base_pursue_duration(self):
		#How long to continue tracking after losing sight of the player
		return 4 * self.INT + 6
		
	def set_target(self, pos):
		if self.has_target():
			self.target_pos.set_to(pos)
		else:
			self.target_pos = pos.copy()
		
	def clear_target(self):
		self.target_pos = None
	
	def has_target(self):
		return self.target_pos is not None
		
	def do_turn(self):
		self.move()
		
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
		
		if self.pack and not one_in(3) and self.set_pack_target_pos():
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
			
		has_los = self.sees(target)
				
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
			return
		
		target = self.target_pos
		
		if (c := g.entity_at(target)) and c.is_player() and self.distance(target) <= 1:
			if self.attack_pos(target):
				return
				
		max_dist = 3 + self.WIS*3//2
		can_path = self.distance(target) <= max_dist and self.path_towards(target)
		
		if not (can_path or self.move_towards(target)):
			self.set_rand_target()
			
	def set_pack_target_pos(self):
		g = self.g	
		x = 0
		y = 0
		num = 0
		
		for mon in g.monsters_in_radius(self.pos, 4):	
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
		
	def alerted(self):
		g = self.g
		board = g.get_board()
		if self.state == "TRACKING":
			self.patience = max(self.patience, random.randint(5, 15) + self.WIS)
		else:
			self.awareness = 0
			if self.pack:
				for mon in g.monsters_in_radius(self.pos, 7):	
					if self.is_ally(mon):
						mon.state == "AWARE"
			if self.state == "IDLE":
				self.state = "AWARE"
	
		
			
	def attack_pos(self, pos):
		g = self.g
		board = g.get_board()
		if not (c := g.entity_at(pos)):
			return False
		
		assert c.is_player() #TODO: Remove when it's possible for monsters to attack other monsters
		
		mod = self.to_hit
		
		if self.pack:
			allies = 0
			for p in board.points_in_radius(self.pos, 1):
				mon = g.monster_at(p)
				if mon and self.is_ally(mon):
					allies += 1
					if allies >= 2:
						break
			if allies > 0:
				bonus = 2.5*allies
				mod += bonus
					
		roll = gauss_roll(mod)
		self.add_msg(f"{roll} vs {c.calc_evasion()}")
		if roll >= c.calc_evasion():
			damage = self.damage.roll()
			damage += div_rand(self.STR - 10, 2)
			damage = max(damage, 1)
			self.add_msg(f"{self.get_name(True)} attacks {c.get_name()}.")
			c.take_damage(damage)
		else:
			self.add_msg(f"{self.get_name(True)}'s attack misses {c.get_name()}.")
		return True
		
	def move(self):
		g = self.g
		board = g.get_board()
		player = g.get_player()
		
		match self.state:
			case "IDLE":
				self.idle()
				if player.sees(self):
					roll = gauss_roll((player.DEX-10)/2)
					perception = 10 + (self.WIS-10)/2
					if roll < perception:
						self.awareness += 1 + perception - roll
						if self.awareness >= random.uniform(3, 6):
							self.alerted()
							self.target_entity(player)
					else:
						self.awareness = max(self.awareness - 1, 0)
					
			case "AWARE":	
				if self.sees(player):
					grouped = False
					if self.pack and self.distance(player) > 2:
						if x_in_y(2, 5):	
							grouped = self.set_pack_target_pos()
					if not grouped:
						self.target_entity(player)
						
					if self.id == "bat" and one_in(5):
						self.set_rand_target()	
					
				else:
					self.state = "TRACKING"
					self.target_entity(player)
					patience = self.base_pursue_duration()	
					self.patience = round(patience * random.triangular(0.8, 1.2))
				
			case "TRACKING":
				loss = 1
				if self.target_pos == self.pos:
					if x_in_y(3, 5):
						self.set_target(player.pos)
					
				self.patience -= loss
				if self.sees(player):
					self.state = "AWARE"
				elif self.patience <= 0:
					self.state = "IDLE"
				
		self.move_to_target()
		
			