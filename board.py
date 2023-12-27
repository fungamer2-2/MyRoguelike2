from utils import *
import random
from collections import defaultdict
from pathfinding import find_path

class Tile:
	
	def __init__(self):
		self.wall = False
		self.revealed = False
		self.stair = 0
		self.items = []
		
	def is_passable(self):
		return not self.wall
		
class Field:
	
	def __init__(self, transparency, decay_rate):
		self.transparency = transparency
		self.decay_rate = decay_rate
		
	def copy(self):
		return Field(self.transparency, self.decay_rate)
		
class DenseFog(Field):
		
	def __init__(self):
		super().__init__(2, 27)
		
fields = {
	"dense_fog": DenseFog
}

class Board:
		
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.clear_grid()
		self.mon_collision_cache = [[None for i in range(width)] for j in range(height)]	
		self.los_cache = [[{} for i in range(width)] for j in range(height)]	
		self.field_map = {}
		self.recalc_sight = False
		
	def field_at(self, pos):
		return self.field_map.get(pos)
		
	def remove_field(self, pos):
		if pos in self.field_map:
			del self.field_map[pos]
			self.recalc_sight = True
		
	def tick_fields(self, subt):
		for pos in list(self.field_map.keys()):
			field = self.field_map[pos]
			if x_in_y(subt, 100):	
				if one_in(field.decay_rate):
					self.remove_field(pos)
					
		
	def add_field(self, pos, name):
		self.put_field(pos, fields[name]())
		self.recalc_sight = True
		
	def set_field(self, pos, radius, name):
		#Perform a flood fill out to radius. This allows it to go around corners, but not through walls
		stack = [pos]
		visited = set()
		while stack:
			p = stack.pop()
			
			if p not in visited:
				visited.add(p)
				if self.passable(p) and p.distance(pos) <= radius:
					self.add_field(p, name)
					stack.extend(self.get_adjacent_tiles(p))
					
		
			
	def put_field(self, pos, field):
		self.field_map[pos] = field	
		
	def place_item_at(self, pos, item):
		self.get_tile(pos).items.append(item)
	
	def clear_grid(self):
		width = self.width
		height = self.height
		self.grid = [[Tile() for _ in range(width)] for _ in range(height)]	
		
	def random_passable(self):
		MAX_TRIES = 6 * self.width * self.height
		for _ in range(MAX_TRIES):
			pos = self.random_pos()
			if self.passable(pos):
				return pos
		raise RuntimeError("Could not find a valid passable position")		
		
	def init_border(self):
		width = self.width
		height = self.height
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
		
		return None
		
	def clear_los_cache(self):
		width = self.width
		height = self.height
		self.los_cache = [[{} for i in range(width)] for j in range(height)]	
		
	def has_line_of_sight(self, pos1, pos2):
		return self._check_simple_los(pos1, pos2) or self._check_simple_los(pos2, pos1)
	
	def has_clear_path(self, pos1, pos2):
		return self._check_simple_clear_path(pos1, pos2) or self._check_simple_clear_path(pos2, pos1)
		
	def _check_simple_los(self, pos1, pos2):
		if pos1 == pos2:
			return True
		
		if (val := self.get_los_cache(pos1, pos2)):
			return val
		old_pos = None
		
		num_field = 0
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
			passable = self.passable(pos)
				
			if not passable:	
				self.set_los_cache(pos1, pos2, False)
				return False
			
			self.set_los_cache(pos1, pos, True)
			old_pos = pos
			
		self.set_los_cache(pos1, pos2, True)
		return True
		
	def field_blocks_view(self, pos1, pos2):
		return self._check_simple_field_blocks(pos1, pos2) and self._check_simple_field_blocks(pos2, pos1)
		
	def _check_simple_field_blocks(self, pos1, pos2):
		if not self.field_map:
			return False
			
		count = 0
		transparency = 9999
		for pos in points_in_line(pos1, pos2):
			if count >= transparency:
				return True
				
			field = self.field_at(pos)
			
			if field and pos != pos1:
				transparency = min(transparency, field.transparency)
				count += 1
		
		return False
		
	def _check_simple_clear_path(self, pos1, pos2):
		if not self.has_line_of_sight(pos1, pos2):
			return False
		old_pos = None
		for pos in points_in_line(pos1, pos2):
			if pos == pos1:
				continue
			if old_pos:
				delta = old_pos - pos
				ad = abs(delta)
				if ad.x == 1 and ad.y == 1:
					blocked = 0
					blocked += self.get_collision_cache(Point(pos.x + delta.x, pos.y)) is not None
					blocked += self.get_collision_cache(Point(pos.x, pos.y + delta.y)) is not None
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
		width = self.width
		height = self.height
		self.mon_collision_cache = [[None for i in range(width)] for j in range(height)]
	
	def random_pos(self):
		x = rng(1, self.width - 1)
		y = rng(1, self.height - 1)
		return Point(x, y)
			
	def set_wall(self, x, y, wall):
		self.grid[y][x].wall = wall
	
	def get_tile(self, pos):
		return self.grid[pos.y][pos.x]
		
	def passable(self, pos):
		if not self.in_bounds(pos):
			return False
		return not self.get_tile(pos).wall
		
	def blocks_sight(self, pos):
		#This is just a placeholder to be extended when other things block sight
		return not self.passable(pos)
		
	def reveal_tile_at(self, pos):
		tile = self.get_tile(pos)
		tile.revealed = True
		
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
			yield point.copy()
			point.x += 1
			if point.x > x2:
				point.x = x1
				point.y += 1
				if point.y > y2:
					break
					
	def points_in_radius(self, center, radius):
		for pos in self.iter_square(center.x-radius, center.y-radius, center.x+radius, center.y+radius):
			if pos.distance(center) <= radius:
				yield pos
			
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
		self.clear_grid()
		self.init_border()
		procgen(self)
	
	def get_fov(self, pos):
		fov = set()
		fov.add(pos)
		
		def cast_line_to(start, end, func):
			count = 0
			transp = 9999
			for p in points_in_line(start, end):
				if not self.has_line_of_sight(start, p):
					break
				if count >= transp:
					break
				func(p)
				field = self.field_at(p)
				if field and p != start:
					transp = min(transp, field.transparency)
					count += 1
						
		width = self.width
		height = self.height
		#Initial raycasting step
		for x in range(width):	
			cast_line_to(pos, Point(x, 0), fov.add)
			cast_line_to(pos, Point(x, height-1), fov.add)
			
			 
		for y in range(1, height-1):
			cast_line_to(pos, Point(0, y), fov.add)
			cast_line_to(pos, Point(width-1, y), fov.add)
		
			
		#Cleanup step - ensure that nearby walls around open spaces are visible
		seen = set()
		for cell in fov.copy():
			if self.blocks_sight(cell):
				continue
			delta = cell - pos
			neighbors = [
				Point(cell.x-1, cell.y),
				Point(cell.x+1, cell.y),
				Point(cell.x, cell.y+1),
				Point(cell.x, cell.y-1)
			]
			for p in neighbors:
				if p in seen or p in fov:
					continue
				
				if not self.in_bounds(p):
					continue
					
				if self.blocks_sight(p):
					can_see = False
					
					d = p - cell
					
					if delta.x <= 0 and delta.y <= 0:
						can_see = d.x <= 0 or d.y <= 0
					if delta.x >= 0 and delta.y <= 0:
						can_see |= d.x >= 0 or d.y <= 0
					if delta.x <= 0 and delta.y >= 0:
						can_see |= d.x <= 0 or d.y >= 0
					if delta.x >= 0 and delta.y >= 0:
						can_see |= d.x >= 0 or d.y >= 0
					
					if can_see:
						seen.add(p)
						fov.add(p)
				
		return fov
		
	def get_path(self, start, end, cost_func=None):
		def passable_func(p):
			return p == start or self.passable(p)
		
		if cost_func is None:
			cost_func = lambda p: 1
			
		return find_path(self, start, end, passable_func, cost_func)
		
		