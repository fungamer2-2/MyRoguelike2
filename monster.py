from entity import Entity
from utils import *
import random

class Monster(Entity):
	
	def __init__(self):
		super().__init__()
		self.symbol = "m"
		
	def do_turn(self):
		if one_in(3):
			self.move()
	
	def move(self):
		board = self.g.get_board()
		adj = board.get_adjacent_tiles(self.pos)	
		random.shuffle(adj)
		
		for pos in adj:
			if self.move_to(pos):
				break
