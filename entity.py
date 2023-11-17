from utils import *

class Entity:
	g = None
	
	def __init__(self):
		self.STR = 10
		self.DEX = 10
		self.CON = 10
		self.INT = 10
		self.HP = self.MAX_HP = 5
		self.pos = Point()
		
	def add_msg(self, text):
		g = self.g
		g.add_message(text)
		
	def can_move_to(self, pos):
		g = self.g
		board = g.get_board()
		return board.passable(pos) and not g.monster_at(pos)
		
	def move_to(self, pos):
		board = self.g.get_board()
		if self.can_move_to(pos):
			old_pos = self.pos
			self.pos = pos
			board.erase_collision_cache(old_pos)
			board.set_collision_cache(pos, self)
			return True
		return False
		
	def move_dir(self, dx, dy):
		return self.move_to(self.pos + Point(dx, dy))
	
	def set_hp(self, HP):
		self.HP = clamp(HP, 0, self.MAX_HP)
		
	def take_damage(self, dam):
		self.set_hp(self.HP - dam)
	
	def is_alive(self):
		return self.HP > 0
		
	def sees(self, other):
		if isinstance(other, Point):
			return board.has_line_of_sight(self.pos, other)
			
		if self is other:
			return True
		board = self.g.get_board()
		return board.has_line_of_sight(self.pos, other.pos)
			
	def has_clear_path(self, pos):
		board = self.g.get_board()
		return board.has_clear_path(self.pos, pos)
			
		
	def display_color(self):
		return 0
		
	def do_turn(self):
		pass