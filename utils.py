import random, math
from random import randint as rng
from itertools import accumulate

def gen_stats():
	stats = [rng(10, 11) for _ in range(6)]
	while True:
		ind1 = rng(0, 5)
		ind2 = rng(0, 5)
		if ind1 == ind2:
			continue
		if not rng(5, 9) <= stats[ind1] <= rng(11, 15):
			continue
		if not rng(5, 9) <= stats[ind2] <= rng(11, 15):
			continue
		
		if not one_in(7):
			stats[ind1] -= 1
		if not one_in(7):
			stats[ind2] += 1
		if one_in(50):
			return stats
	
def rng_float(a, b):
	if a > b:
		a, b = b, a
	return random.uniform(a, b)
	
def triangular_roll(a, b):
	#Returns a rand integer between a and b inclusive, biased towards the average result
	range = b - a
	r1 = range//2
	r2 = (range+1)//2
	
	return a + rng(0, r1) + rng(0, r2)

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

def mult_rand_frac(val, x, y):
	return div_rand(val * x, y)
	
def stat_mod(stat):
	return (stat - 10) / 2 

def random_weighted(entries):
	values, weights = list(zip(*entries))
	return random.choices(values, weights=weights)[0]
	
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
	
def apply_armor(damage, armor):
	prot = rng(0, 2 * armor)
	return max(damage - prot, 0)
	
def calc_ranged_penalty(r, short, long):
	if r <= short:
		return 0.0
	return 5 * (r - short) / (long - short)
	
	
class WeightedList:
	
	def __init__(self):
		self.choices = []
		self.weights = []
		self.cumulative_weights = None
		
	def add(self, value, weight):
		if weight > 0:
			self.choices.append(value)
			self.weights.append(weight)
			self.cumulative_weights = None 
	
	def clear(self):
		self.choices.clear()
		self.weights.clear()
		self.cumulative_weights = None 
		
	def pick(self):
		if len(self.choices) == 0:
			raise IndexError("cannot pick from an empty weighted list")
		if not self.cumulative_weights:
			self.cumulative_weights = list(accumulate(self.weights))
		return random.choices(self.choices, cum_weights=self.cumulative_weights)[0]

	
class Dice:
		
	def __init__(self, num, sides, mod=0):
		self.num = num
		self.sides = sides
		self.mod = mod
		
	def roll(self):
		return dice(self.num, self.sides) + self.mod
		
	def __str__(self):
		s = f"{self.num}d{self.sides}"
		if self.mod != 0:
			s += f"+{self.mod}" if self.mod > 0 else str(self.mod)
		return s
	
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
		
	def square_dist(self, other):
		abs_d = abs(other - self)
		return max(abs_d.x, abs_d.y)
		
def points_in_line(p1, p2, d=0):
	x1 = p1.x
	y1 = p1.y
	x2 = p2.x
	y2 = p2.y	
	
	dx = abs(x2 - x1)
	sx = 1 if x1 < x2 else -1
	dy = -abs(y2 - y1)
	sy = 1 if y1 < y2 else -1
	error = dx + dy + d
	
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