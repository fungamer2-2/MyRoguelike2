from utils import Point, points_in_line
import random
from collections import defaultdict

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
		self.los_cache = [[{} for i in range(width)] for j in range(height)]	
		
		
		for x in range(width):
			self.set_wall(x, 0, True)
			self.set_wall(x, height-1, True)
		for y in range(1, height-1):
			self.set_wall(0, y, True)
			self.set_wall(width-1, y, True) 		
		
	def set_los_cache(self, pos1, pos2, has_los):
		cache1 = self.los_cache[pos1.y][pos1.x]
		cache1[pos2.copy()] = has_los
		
	def get_los_cache(self, pos1, pos2):
		cache1 = self.los_cache[pos1.y][pos1.x]
		if (val := cache1.get(pos2)):
			return val
		cache2 = self.los_cache[pos2.y][pos2.x]
		if (val := cache2.get(pos1)):
			return val
		return None
		
	def clear_los_cache(self):
		self.los_cache = [[{} for i in range(width)] for j in range(height)]	
			
	def has_line_of_sight(self, pos1, pos2):
		if pos1 == pos2:
			return True
		if pos1.x < pos2.x:
			pos1, pos2 = pos2, pos1
		elif pos1.x == pos2.x:
			if pos1.y > pos2.y:
				pos1, pos2 = pos2, pos1
			
		if (val := self.get_los_cache(pos1, pos2)):
			return val
		old_pos = None
		for pos in points_in_line(pos1, pos2):
			if old_pos:
				delta = old_pos - pos
				ad = abs(delta)
				if ad.x == 1 and ad.y == 1:
					blocked = 0
					blocked += not self.passable(Point(pos.x + delta.x, pos.y))
					blocked += not self.passable(Point(pos.x, pos.y + delta.y))
					if blocked >= 2:
						self.set_los_cache(pos1, pos, False)
						return False
			if pos == pos2:
				break
			passable = self.passable(pos)	
			if not passable:	
				self.set_los_cache(pos1, pos, False)
				return False
			
			self.set_los_cache(pos1, pos, True)
			old_pos = pos
			
		self.set_los_cache(pos1, pos2, True)
		return True
		
	def has_clear_path(self, pos1, pos2):
		if not self.has_line_of_sight(pos1, pos2):
			return False
		old_pos = None
		for pos in points_in_line(pos1, pos2):
			if old_pos:
				delta = old_pos - pos
				ad = abs(delta)
				if ad.x == 1 and ad.y == 1:
					blocked = 0
					blocked += not self.get_collision_cache(Point(pos.x + delta.x, pos.y))
					blocked += not self.get_collision_cache(Point(pos.x, pos.y + delta.y))
					if blocked >= 2:
						return False
			if pos == pos2:
				break
			passable = self.get_collision_cache(pos) is None
			if not passable:
				return False
			old_pos = pos
			
		return True
		
			
			
	def set_collision_cache(self, pos, val):
		self.mon_collision_cache[pos.y][pos.x] = val
		
	def get_collision_cache(self, pos):
		return self.mon_collision_cache[pos.y][pos.x]
		
	def erase_collision_cache(self, pos):
		self.set_collision_cache(pos, None)
			
	def clear_collision_cache(self):
		self.mon_collision_cache = [[None for i in range(width)] for j in range(height)]
	
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
		