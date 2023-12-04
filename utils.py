import random, math

from random import randint as rng

def gen_stats():
	points = 27
	stats = [8] * 6
	
	ind = -1
	while points > 0:
		eligible = [i for i in range(6) if stats[i] < 15]	
		if ind == -1:
			ind = random.choice(eligible)
		cost = 2 if stats[ind] >= 13 else 1
		if points < cost:
			ind = -1
			continue
		stats[ind] += 1
		points -= cost
		
		if stats[ind] >= 15 or random.randint(1, 2) == 1:
			ind = -1
			
	return stats

def gauss_roll(mod):
	return random.gauss(10 + mod, 5)
	
def gauss_cdf(mean, stdev, x):
	return 0.5 * (1 + math.erf((x - mean)/(stdev*math.sqrt(2))))
	
def gauss_roll_prob(mod, DC):
	cdf = gauss_cdf(10 + mod, 5, DC)
	return (1 - cdf) * 100
	
def clamp(val, lo, hi):
	return max(lo, min(val, hi))
	
def one_in(x):
	return x <= 1 or rng(1, x) == 1
	
def x_in_y(x, y):
	return random.uniform(0.0, y) < x
	
def div_rand(x, y):
	"Computes x/y then randomly rounds the result up or down depending on the remainder"
	sign = 1
	if (x > 0) ^ (y > 0):
		sign = -1
	x = abs(x)
	y = abs(y)
	mod = x % y
	return sign * (x//y + (rng(1, y) <= mod))
 
	
def dice(num, sides):
	if sides == 1:
		return num
	return sum(rng(1, sides) for _ in range(num))

def gen_stat():
	vals = [rng(1, 6) for _ in range(4)]
	return sum(vals) - min(vals)	

def display_bar(val, max, width):
	val = clamp(val, 0, max)
	part = width * val / max
	num = int(part)
	string = []
	
	bars = "|"*num
	rem = part - int(part)
	if 0 < val < max and (num <= 0 or rem >= 0.5):
		bars += "."
	bars += " "*(width-len(bars))
	return f"[{bars}]"
	
class Dice:
		
	def __init__(self, num, sides, mod):
		self.num = num
		self.sides = sides
		self.mod = mod
		
	def roll(self):
		return dice(self.num, self.sides) + self.mod
		
	
class Point:
	
	def __init__(self, x=0, y=0):
		self.set(x, y)
		
	def set(self, x, y):
		self.x = x
		self.y = y
		
	def set_to(self, other):
		self.x = other.x
		self.y = other.y
		
	def __repr__(self):
		return f"({self.x}, {self.y})"
		
	def __add__(self, other):
		if isinstance(other, Point):
			return Point(self.x + other.x, self.y + other.y)
		return NotImplemented
		
	def __iadd__(self, other):
		if isinstance(self, Point):
			self.x += other.x
			self.y += other.y
			return self
		return NotImplemented
		
	def __sub__(self, other):
		if isinstance(other, Point):
			return Point(self.x - other.x, self.y - other.y)
		return NotImplemented
		
	def __isub__(self, other):
		if isinstance(other, Point):
			self.x -= other.x
			self.y -= other.y
			return self
		return NotImplemented
		
	def __neg__(self):
		return Point(-self.x, -self.y)
		
	def __abs__(self):
		return Point(abs(self.x), abs(self.y))
		
	def as_tuple(self):
		return (self.x, self.y)
		
	def copy(self):
		return Point(self.x, self.y)
		
	def __hash__(self):
		return hash((self.x, self.y))
		
	def __eq__(self, other):
		if isinstance(other, Point):
			return self.x == other.x and self.y == other.y
		return False
		
	def distance(self, other):
		delta = other - self
		return abs(delta.x) + abs(delta.y)	
	
def points_in_line(p1, p2):
	x1 = p1.x
	y1 = p1.y
	x2 = p2.x
	y2 = p2.y	
	
	dx = abs(x2 - x1)
	sx = 1 if x1 < x2 else -1
	dy = -abs(y2 - y1)
	sy = 1 if y1 < y2 else -1
	error = dx + dy
	
	pos = Point(x1, y1)
	endpos = Point(x2, y2)
	while True:
		yield pos.copy()
		if pos == endpos:
			break
		e2 = 2 * error
		if e2 >= dy:
			if pos.x == x2:
				break
			error += dy
			pos.x += sx
		if e2 <= dx:
			if pos.y == y2:
				break
			error += dx
			pos.y += sy