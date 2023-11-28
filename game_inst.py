from json_obj import load_monster_types
from board import Board
from entity import Entity
from monster import Monster
from player import Player
from messages import MessageLog
from const import *
from utils import *	
import curses, textwrap

class Game:
	
	def __init__(self):
		self._board = Board(50, 18)
		self._player = Player()
		self.screen = None
		self.monsters = []
		self.msg_log = MessageLog(MESSAGE_LOG_CAPACITY)
		self.window_init = True
		self.mon_types = {}
		self.level = 1
		
	def check_mon_type(self, typ):
		if typ not in self.mon_types:
			valid_types = sorted(self.mon_types.keys())
			error = ValueError(f"invalid monster type {typ!r}")
			error.add_note(f"Valid monster types are: {', '.join(valid_types)}")
			raise error
		
	def get_mon_type(self, typ):
		self.check_mon_type(typ)
		return self.mon_types[typ]
		
	def get_all_monster_types(self):
		for typ in self.mon_types.values():
			yield typ
		
	def add_message(self, text):
		self.msg_log.add_message(text)
		
	def init_game(self):
		self.screen = curses.initscr()
		curses.start_color()
		assert curses.has_colors()
		
		curses.noecho()
		curses.curs_set(False)
		Entity.g = self
		self.load_monsters()
		
		self.generate_level()	
		self.draw_board()
		
	def generate_level(self):
		board = self.get_board()
		
		self.monsters.clear()
		board.clear_los_cache()
		board.clear_collision_cache()
		board.procgen_level()
		self.place_player()
		self.place_monsters()
		
	def place_monsters(self):
		eligible_types = []
		for typ in self.get_all_monster_types():
			if self.level >= typ.level:
				eligible_types.append(typ)
		assert len(eligible_types) > 0
			
		num_monsters = rng(3, 5)
		num_monsters += rng(0, round(self.level ** 0.6))
		for _ in range(num_monsters):
			self.place_monster("bat")
		
		
	def deinit_window(self):
		if not self.window_init:
			return
			
		screen = self.screen
		screen.nodelay(False)	
		screen.clear()
		curses.nocbreak()
		curses.echo()
		curses.curs_set(True)
		curses.endwin()
		import os
		os.system("cls" if os.name == "nt" else "clear")
		self.window_init = False
		
	def place_player(self):
		board = self.get_board()
		player = self.get_player()
		while True:
			pos = board.random_pos()
			if board.passable(pos):
				break
		player.move_to(pos)
		board.set_collision_cache(pos, player)
		
	def place_monster_at(self, typ_id, pos):
		typ = self.get_mon_type(typ_id)
		m = Monster.from_type(typ)
		board = self.get_board()
		if m.move_to(pos):
			board.set_collision_cache(pos, m)
			self.monsters.append(m)
			return m
		return None
		
	def place_monster(self, typ_id):
		typ = self.get_mon_type(typ_id)
		board = self.get_board()
		
		found_pos = None
		if typ.pack_travel and len(self.monsters) > 2 and not one_in(4):
			pos = random.choice(self.monsters).pos
			candidates = []
			for p in board.points_in_radius(pos, 3):
				if not board.has_line_of_sight(p, pos):
					continue
				if not self.monster_at(p):
					if one_in(pos.distance(p)):
						candidates.append(p)
			if candidates:
				found_pos = random.choice(candidates)	
		
		if not found_pos:	
			for tries in range(150):
				pos = board.random_pos()
				if board.passable(pos) and not self.monster_at(pos):
					found_pos = pos
					break
			if not found_pos:
				return None
		
		return self.place_monster_at(typ_id, found_pos)
		
	def load_monsters(self):
		self.mon_types = load_monster_types()
		
	def entity_at(self, pos):
		board = self.get_board()
		return board.get_collision_cache(pos)
		
	def monster_at(self, pos):
		entity = self.entity_at(pos)
		if isinstance(entity, Player):
			return None
		return entity
		
	def monsters_in_radius(self, pos, radius):
		board = self.get_board()
		for pos in board.points_in_radius(pos, radius):
			if (mon := self.monster_at(pos)) and not isinstance(mon, Player):
				yield mon
			
	def get_board(self):
		return self._board
		
	def get_player(self):
		return self._player
	
	def do_turn(self):
		board = self.get_board()
		self.refresh_mon_pos_cache()
		player = self.get_player()
		player.do_turn()
		need_rebuild = False
		for m in self.monsters:
			if m.is_alive():
				m.do_turn()
				expected = m.pos
			else:
				board.erase_collision_cache(m.pos)
				expected = None
			
		self.remove_dead()
		
	def refresh_mon_pos_cache(self):
		board = self.get_board()
		player = self.get_player()
		board.clear_collision_cache()
		
		board.set_collision_cache(player.pos, player)	
		for m in self.monsters:
			board.set_collision_cache(m.pos, m)
		
	def remove_dead(self):
		board = self.get_board()
		for m in reversed(self.monsters):
			if not m.is_alive():
				self.monsters.remove(m)
			
	def get_char(self, wait=True):
		screen = self.screen
		screen.nodelay(not wait)
		if wait:
			curses.flushinp()
			
		code = screen.getch()
		if code == -1:
			return None
		
		return chr(code)
	
	def draw_symbol(self, row, col, symbol, color=0):
		screen = self.screen
		rows, cols = screen.getmaxyx()
		
		if 0 <= row < rows and 0 <= col < cols:
			screen.addstr(row, col, symbol, color)
		
	def draw_string(self, row, col, string):
		screen = self.screen
		rows, cols = screen.getmaxyx() 
		if col >= cols or not (0 <= row < rows):
			return
		diff = cols - (col + len(string))
		if diff < 0:
			string = string[:diff]
		screen.addstr(row, col, string)	 
		
	def draw_walls(self, offset_y):	
		board = self.get_board()
		player = self.get_player()
		height = board.height
		width = board.width
		player = self.get_player()
		
		for pos in board.iter_square(0, 0, width-1, height-1):
			tile = board.get_tile(pos)
			if not tile.revealed:
				symbol = " "
			elif tile.wall:
				symbol = WALL_SYMBOL
			else:
				symbol = "." if player.sees(pos) else " "
			
			self.draw_symbol(pos.y + offset_y, pos.x, symbol)
			
			
	def draw_stats(self):
		board = self.get_board()
		height = board.height
		width = board.width
		player = self.get_player()
		
		bar = "HP: " + display_bar(player.HP, player.MAX_HP, 20)			
		p = f"({player.HP}/{player.MAX_HP})".ljust(12)
		bar += " " + p
		self.draw_string(0, 0, bar)
		
		strings = [
			f"STR {player.STR}",
			f"DEX {player.DEX}",
			f"CON {player.CON}"
		]
		for i in range(len(strings)):
			padded = strings[i].ljust(6)
			self.draw_string(i, width + 6, padded)	

	def draw_monsters(self, offset_y):
		player = self.get_player()
		for m in self.monsters:
			pos = m.pos
			color = 0
			symbol = " "
			if player.sees(m):
				symbol = m.symbol 
				if m.state == "IDLE":
					color = curses.A_REVERSE
			
			self.draw_symbol(pos.y + offset_y, pos.x, symbol, color)	
		
		pos = player.pos
		self.draw_symbol(pos.y + offset_y, pos.x, PLAYER_SYMBOL, curses.A_REVERSE)
	
	def draw_messages(self, offset_y):
		screen = self.screen
		
		messages = self.msg_log.get_messages(8)
		board = self.get_board()
		y = board.height + offset_y
		rows, cols = screen.getmaxyx()
		groups = []
		
		total_lines = 0
		for message in reversed(messages):
			group = textwrap.wrap(message, width=cols)
			groups.append(group)
			total_lines += len(group)
			if total_lines >= 8:
				break
		groups.reverse()
		
		displayed = []
		for group in groups:
			displayed.extend(group)
		displayed = displayed[-8:] 
			
		for i in range(len(displayed)):
			msg = displayed[i]
			padded = msg.ljust(cols)
			self.draw_string(y + i, 0, padded)			

	def reveal_seen_tiles(self):
		board = self.get_board()
		player = self.get_player()
		for pos in player.fov:
			board.reveal_tile_at(pos)
			
	def draw_board(self):
		screen = self.screen
		offset_y = 1
		
		self.reveal_seen_tiles()
		self.draw_walls(offset_y)
		self.draw_monsters(offset_y)
		self.draw_stats()
		self.draw_messages(offset_y)
		screen.move(20 + offset_y, 0)
		screen.refresh()
	
	def process_key_input(self, char):
		player = self.get_player()
		if char == "w":
			return player.move_dir(0, -1)
		if char == "s":
			return player.move_dir(0, 1)
		elif char == "a":
			return player.move_dir(-1, 0)
		elif char == "d":
			return player.move_dir(1, 0)
		elif char == " ":
			return True
		
		return False
	
	def game_over(self):
		pass