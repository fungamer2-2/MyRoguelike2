import random, math

def gauss_roll(mod):
	return random.gauss(10 + mod, 5)
	
def gauss_cdf(mean, stdev, x):
	return 0.5 * (1 + math.erf((x - mean)/(stdev*math.sqrt(2))))
	
def gauss_roll_prob(mod, DC):
	cdf = gauss_cdf(10 + mod, 5, DC)
	return 1 - cdf
	
def clamp(val, lo, hi):
	return max(lo, min(val, hi))
	
def one_in(x):
	return x <= 1 or random.randint(1, x) == 1
	
def x_in_y(x, y):
	return random.uniform(0.0, y) < x
	
def dice(num, sides):
	return sum(random.randint(1, sides) for _ in range(num))

def gen_stat():
	vals = [random.randint(1, 6) for _ in range(4)]
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
		return f"Point({self.x}, {self.y})"
		
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