import random
from copy import deepcopy
from utils import Point
from pathfinding import find_path

def count_neighbors(grid, x, y):
	w = len(grid[0])
	h = len(grid)
	num = 0
	if x > 0:
		num += grid[y][x-1]	
	if x < w - 1:
		num += grid[y][x+1]
	if y > 0:
		num += grid[y-1][x]
	if y < h - 1:
		num += grid[y+1][x]
	
	if x > 0 and y > 0:
		num += grid[y-1][x-1]
	if x > 0 and y < h - 1:
		num += grid[y+1][x-1]	
	if x < w - 1 and y > 0:
		num += grid[y-1][x+1]	
	if x < w - 1 and y < h - 1:
		num += grid[y+1][x+1]	
	
	return num
	
def flood_fill(grid, x, y, pred):
	visited = set()
	stack = [(x, y)]
	w = len(grid[0])
	h = len(grid)
	
	while stack:
		pos = stack.pop()
		if pos in visited:
			continue
		visited.add(pos)
		xp, yp = pos
		if grid[yp][xp] == 0:
			
			pred(xp, yp)
			if xp > 0:
				stack.append((xp-1, yp))
			if xp < w - 1:
				stack.append((xp+1, yp))
			if yp > 0:
				stack.append((xp, yp-1))
			if yp < h - 1:
				stack.append((xp, yp+1))
				
def cellular_automata_pass(grid):
	w = len(grid[0])
	h = len(grid)
	c = deepcopy(grid)
	for y in range(h):
		for x in range(w):
			num = count_neighbors(c, x, y) 
			if c[y][x] == 1:
				if num < 3:
					grid[y][x] = 0
			elif c[y][x] == 0:
				if num > 4:
					grid[y][x] = 1
					
def find_disconnected_zones(grid):
	w = len(grid[0])
	h = len(grid)
	
	empty = set()
						
	for y in range(h):
		for x in range(w):
			if grid[y][x] == 0:
				empty.add((x, y))
	
	curr = []
	zones = []
				
	def func(xp, yp):
		curr.append(Point(xp+1, yp+1))
		empty.discard((xp, yp))
				
	
	while empty:
		x, y = empty.pop()	
		curr = []
		flood_fill(grid, x, y, func)
		zones.append(curr)
	
	return zones
		
def procgen(board):
	width = board.width
	height = board.height
	grid = [[0 for i in range(width-2)] for j in range(height-2)]
	
	#Initialize the base randomly
	p = random.triangular(45, 55)
	for y in range(height-2):
		for x in range(width-2):
			if random.uniform(0, 100) < p:
				grid[y][x] = 1	
	
	iters = random.randint(3, 4) + random.randint(0, 4)
	for _ in range(iters):
		cellular_automata_pass(grid)
						
	zones = find_disconnected_zones(grid)
	
	for pos in board.iter_square(1, 1, width-2, height-2):
		tile = board.get_tile(pos)
		x, y = pos.as_tuple()
		tile.wall = bool(grid[pos.y-1][pos.x-1])
			
	assert len(zones) > 0
	if len(zones) <= 1:
		return
		
	def passable_func(pos):
		return (1 <= pos.x < board.width - 1) and (1 <= pos.y < board.height - 1)
	
	cost_func = lambda pos: 0.5 if board.get_tile(pos).wall else 1
		
	for i in range(len(zones)):
		p1 = random.choice(zones[i])
		if i < len(zones) - 1:
			p2 = random.choice(zones[i + 1])
		else:
			zone = zones[random.randint(0, len(zones) - 1)]
			p2 = random.choice(zone)	
		path = find_path(board, p1, p2, passable_func, cost_func)
		
		for pos in path:
			tile = board.get_tile(pos)
			tile.wall = False
			
	
		