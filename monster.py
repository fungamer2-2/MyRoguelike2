from entity import Entity
from utils import *
from pathfinding import find_path
from collections import deque
import random

class Monster(Entity):
	
	def __init__(self):
		super().__init__()
		self.symbol = "m"
		self.target_pos = None
		self.state = "IDLE"
		self.patience = 0
		self.INT = 10
		self.path = deque()
		
	def calc_path_to(self, pos):
		g = self.g
		board = g.get_board()
		def passable_func(p):
			return p == pos or self.can_move_to(p)
		
		cost_func = lambda p: 1
		path = find_path(board, self.pos, pos, passable_func, cost_func)
		
		self.path.clear()
		if not path:
			return
		del path[0] #Remove start position		
		self.path.extend(path)
		
	def path_towards(self, pos):
		if self.pos == pos:
			self.path.clear()
			return
		
		if self.path:
			if pos != self.path[-1] or not self.move_to(self.path.popleft()):
				self.calc_path_to(pos)
				if self.path:
					self.move_to(self.path.popleft())
		else:
			self.calc_path_to(pos)
			
			if self.path:
				self.move_to(self.path.popleft())	
			
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
		if not one_in(3):
			self.move()
			
	def idle(self):
		g = self.g
		board = g.get_board()
		adj = board.get_adjacent_tiles(self.pos)	
		random.shuffle(adj)
		
		for pos in adj:
			if self.can_move_to(pos):
				self.set_target(pos)
				break
				
	def move_towards(self, target):
		g = self.g
		board = g.get_board()
		
		delta = target - self.pos		
		dx = delta.x
		dy = delta.y
		if dx != 0:
			dx //= abs(dx)
		if dy != 0:
			dy //= abs(dy)
				
		d = abs(delta)			
		move_x = x_in_y(d.x, d.x + d.y) #Randomize, weighted by the x and y difference to the target
				
		pos = self.pos
		if move_x:
			#If moving in one direction would break line of sight, 
			t = Point(pos.x + dx, pos.y)
			maintains_los = board.has_line_of_sight(t, target)	
			if not (maintains_los and self.move_dir(dx, 0)): #If one direction doesn't work, try the other
				self.move_dir(0, dy)
		else:
			t = Point(pos.x, pos.y + dy)
			maintains_los = board.has_line_of_sight(t, target)	
			if not (maintains_los and self.move_dir(0, dy)):
				self.move_dir(dx, 0)

	def move_to_target(self):
		if not self.has_target():
			return
			
		target = self.target_pos	
		if self.has_clear_path(target):
			self.move_towards(target)
		else:
			self.path_towards(target)
			
	def move(self):
		g = self.g
		board = g.get_board()
		player = g.get_player()
		
		match self.state:
			case "IDLE":
				self.idle()
				if self.sees(player):
					self.state = "AWARE"
					self.set_target(player.pos)
			case "AWARE":
				self.set_target(player.pos)
				if not self.sees(player):
					self.state = "TRACKING"
					patience = self.base_pursue_duration()	
					self.patience = round(patience * random.triangular(0.5, 1.5))
			case "TRACKING":
				if self.target_pos == self.pos:
					if x_in_y(3, 5):
						self.set_target(player.pos)
					else:
						self.patience -= 1
				self.patience -= 1
				if self.sees(player):
					self.state = "AWARE"
				elif self.patience <= 0:
					self.state = "IDLE"
				
		self.move_to_target()
		
			