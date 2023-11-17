from entity import Entity
from utils import *
from pathfinding import find_path
import random

class Monster(Entity):
	
	def __init__(self):
		super().__init__()
		self.symbol = "m"
		self.target_pos = None
		self.state = "IDLE"
		self.patience = 0
		
	def base_pursue_duration(self):
		#How long to continue tracking after losing sight of the player
		return 3 * self.INT + 7
		
	def set_target(self, pos):
		self.target_pos.set_to(pos)
		
	def clear_target(self):
		self.target = None
	
	def has_target(self):
		return self.target is None
		
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

	def move_to_target(self):
		if not self.has_target():
			return
			
		
		g = self.g
		board = g.get_board()
		
		target = self.target_pos
		
		if self.sees(target):
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
		else:
			#TODO: Pathfinding
			pass
			
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
					self.state = "IDLE"
					patience = self.base_pursue_duration()	
					self.patience = round(patience * random.triangular(0.5, 1.5))
			case "TRACKING":
				if self.target_pos == pos:
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
		
			