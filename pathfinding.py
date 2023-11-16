from collections import defaultdict
import random
from utils import Point

class OpenSet:
	
	def __init__(self, key=None):
		self._data = []
		self._dup = set()
		self.key = key or (lambda v: v)
		
	def add(self, value):
		if value in self._dup:
			return
		self._dup.add(value)
		a = self._data
		key = self.key
		i = len(a)
		a.append(value)
		while i > 0:
			parent = i // 2
			if key(a[parent]) < key(a[i]):
				break
			a[parent], a[i] = a[i], a[parent]
			i = parent
			
	def pop(self):
		if len(self._data) == 0:
			raise IndexError("pop from an empty heap")
		a = self._data
		val = a[0]
		a[0] = a[-1]
		a.pop()
		key = self.key
		i = 0
		while True:
			left = 2 * i + 1
			right = 2 * i + 2
			if left >= len(a):
				break
			node = left
			if right < len(a) and key(a[right]) < key(a[left]):
				node = right
			if key(a[i]) > key(a[node]):
				a[i], a[node] = a[node], a[i]
				i = node
			else:
				break
		self._dup.remove(val)
		return val
		
	def __contains__(self, value):
		return value in self._dup
		
	def __bool__(self):
		return len(self._data) > 0
		
def h(p1, p2):
	delta = p1 - p2
	return abs(delta.x) + abs(delta.y)
	
def reconstruct_path(came_from, curr):
	path = [curr]
	while curr in came_from:
		curr = came_from[curr]
		path.append(curr)
	path.reverse()
	return path
		
def find_path(board, start, end, passable_func, cost_func):
	gScore = defaultdict(lambda: float("inf"))
	gScore[start] = 0
	fScore = defaultdict(lambda: float("inf"))
	fScore[start] = h(start, end)
	open_set = OpenSet(fScore.__getitem__)
	open_set.add(start)
	came_from = {}
	width = board.width
	height = board.height	
	while open_set:
		curr = open_set.pop()
		if curr == end:
			return reconstruct_path(came_from, curr)
		neighbors = []
		x, y = curr.as_tuple()
		if x > 0 and passable_func((c := Point(x - 1, y))):
			neighbors.append(c)
		if x < width - 1 and passable_func((c := Point(x + 1, y))):
			neighbors.append(c)
		if y > 0 and passable_func((c := Point(x, y - 1))):
			neighbors.append(c)
		if y < height - 1 and passable_func((c := Point(x, y + 1))):
			neighbors.append(c)	
		random.shuffle(neighbors)		
		for n in neighbors:
			t = gScore[curr] + cost_func(n)
			if t < gScore[n]:
				came_from[n] = curr
				gScore[n] = t
				fScore[n] = t + h(n, end)
				if n not in open_set:
					open_set.add(n)	
	return []
		