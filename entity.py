from utils import *
from const import *
from abc import abstractmethod, ABC

class Entity(ABC):
	g = None
	
	def __init__(self):
		self.STR = 10
		self.DEX = 10
		self.CON = 10
		self.INT = 10
		self.WIS = 10
		self.CHA = 10
		self.HP = self.MAX_HP = 10
		self.pos = Point()
		self.energy = 100
		self.poison = 0
		self.status = {}
		
	def has_status(self, name):
		return name in self.status
		
	def add_status(self, name, dur):
		if not self.has_status(name):
			self.status[name] = 0
		self.status[name] += dur*100
		
	def remove_status(self, name):
		if self.has_status(name):
			del self.status[name]
		
	def use_energy(self, amount):
		self.energy -= amount
		
	def is_player(self):
		return False
		
	def is_monster(self):
		return False
		
	def calc_evasion(self):
		dex = self.DEX
		if not self.is_alive():
			dex = 0
		return 10 + (dex - 10) / 2
		
	def base_speed(self):
		return 100
	
	def get_speed(self):
		return round(self.base_speed() * self.speed_mult())
		
	def speed_mult(self):
		mult = 1
		if self.has_status("Slowed"):
			mult = 0.5
		return mult
		
	def can_act(self):
		return self.energy > 0 and not self.has_status("Paralyzed")
		
	def get_armor(self):
		return 0
	
	@abstractmethod
	def get_name(self, capitalize=False):
		return "Unknown Entity"
		
	def add_msg(self, text, typ="neutral"):
		g = self.g
		g.add_message(text, typ)
		
	def add_msg_u_or_mons(self, u_msg, mon_msg, typ="neutral"):
		g = self.g
		player = g.get_player()
		if self.is_player():
			self.add_msg(u_msg, typ)
		elif self.is_monster() and player.sees(self):
			self.add_msg(mon_msg, typ)
		
	def add_msg_if_u_see(self, other, text, typ="neutral"):
		g = self.g
		player = g.get_player()
		if player.sees(other):
			self.add_msg(text, typ)
		
	def can_move_to(self, pos):
		g = self.g
		board = g.get_board()
		if pos == self.pos:
			return True
		return board.passable(pos) and not g.entity_at(pos)
		
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
		if dam > 0:
			self.set_hp(self.HP - dam)
		
	def heal(self, amount):
		if amount > 0:
			self.set_hp(self.HP + amount)
	
	def is_alive(self):
		return self.HP > 0
		
	def distance(self, other):
		if isinstance(other, Point):
			return self.pos.distance(other)
		return self.pos.distance(other.pos)
		
	def sees_pos(self, pos):
		board = self.g.get_board()
		return board.has_line_of_sight(self.pos, pos)
		
	def sees(self, other):	
		if self is other:
			return True
		
		return self.sees_pos(other.pos)
			
	def has_clear_path(self, pos):
		board = self.g.get_board()
		return board.has_clear_path(self.pos, pos)		
		
	def display_color(self):
		return 0
		
	def do_turn(self):
		pass
		
	def make_noise(self, volume):
		g = self.g
		g.add_noise_event(self.pos, volume)
		
	def roll_wisdom(self):
		mod = (self.WIS-10)/2
		return gauss_roll(mod)