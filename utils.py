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
		
	def as_tuple(self):
		return (self.x, self.y)
		
	def copy(self):
		return Point(self.x, self.y)
		
	def __hash__(self):
		return hash((self.x, self.y))
		
	def __eq__(self, other):
		if isinstance(other, Point):
			return self.x == other.x and self.y == other.y

