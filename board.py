from utils import Point
import random

class Tile:
	
	def __init__(self):
		self.wall = False
		
	def is_passable(self):
		return not self.wall	

class Board:
		
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.grid = [[Tile() for _ in range(width)] for _ in range(height)]
		self.mon_collision_cache = [[None for i in range(width)] for j in range(height)]	
		
		for x in range(width):
			self.set_wall(x, 0, True)
			self.set_wall(x, height-1, True)
		for y in range(1, height-1):
			self.set_wall(0, y, True)
			self.set_wall(width-1, y, True)
			
	def set_collision_cache(self, pos, val):
		self.mon_collision_cache[pos.y][pos.x] = val
		
	def get_collision_cache(self, pos):
		return self.mon_collision_cache[pos.y][pos.x]
		
	def erase_collision_cache(self, pos):
		self.set_collision_cache(pos, None)
			
	def random_pos(self):
		x = random.randint(1, self.width - 1)
		y = random.randint(1, self.height - 1)
		return Point(x, y)
			
	def set_wall(self, x, y, wall):
		self.grid[y][x].wall = wall
	
	def get_tile(self, pos):
		return self.grid[pos.y][pos.x]
		
	def passable(self, pos):
		if not self.in_bounds(pos):
			return False
		return not self.get_tile(pos).wall
		
	def in_bounds(self, pos):
		if pos.x < 0 or pos.x >= self.width:
			return False
		if pos.y < 0 or pos.y >= self.height:
			return False
		return True
		
	def iter_square(self, x1, y1, x2, y2):
		point = Point(x1, y1)
		x1 = max(x1, 0)
		y1 = max(y1, 0)
		x2 = min(x2, self.width - 1)
		y2 = min(y2, self.height - 1)
		
		while True:
			yield point
			point.x += 1
			if point.x > x2:
				point.x = x1
				point.y += 1
				if point.y > y2:
					break
					
	def get_adjacent_tiles(self, pos):
		adj = []
		if self.passable(c := Point(pos.x - 1, pos.y)):
			adj.append(c)
		if self.passable(c := Point(pos.x + 1, pos.y)):
			adj.append(c)
		if self.passable(c := Point(pos.x, pos.y - 1)):
			adj.append(c)
		if self.passable(c := Point(pos.x, pos.y + 1)):
			adj.append(c)
		return adj
					
	def procgen_level(self):
		from procgen import procgen
		procgen(self)
		