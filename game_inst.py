from board import Board
from entity import Entity
from monster import Monster
from player import Player
from messages import MessageLog
from const import *
import curses, textwrap

class Game:
	
	def __init__(self):
		self._board = Board(50, 18)
		self._player = Player()
		self.screen = curses.initscr()
		self.monsters = []
		self.msg_log = MessageLog(MESSAGE_LOG_CAPACITY)
		self.window_init = True
		
	def add_message(self, text):
		self.msg_log.add_message(text)
		
	def init_game(self):
		curses.noecho()
		curses.curs_set(False)
		Entity.g = self
		board = self.get_board()
		board.procgen_level()
		self.place_player()
		for _ in range(5):
			self.place_monster(Monster())		
		self.draw_board()
		
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
		
	def place_monster_at(self, m, pos):
		board = self.get_board()
		if m.move_to(pos):
			board.set_collision_cache(pos, m)
			self.monsters.append(m)
			return True
		return False
		
	def place_monster(self, m):
		board = self.get_board()
		for tries in range(100):
			pos = board.random_pos()
			if board.passable(pos) and not self.monster_at(pos):
				break
		else:
			return False
		
		return self.place_monster_at(m, pos)
		
	def monster_at(self, pos):
		board = self.get_board()
		return board.get_collision_cache(pos)
			
	def get_board(self):
		return self._board
		
	def get_player(self):
		return self._player
	
	def do_turn(self):
		board = self.get_board()
		player = self.get_player()
		player.do_turn()
		for m in self.monsters:
			if m.is_alive():
				m.do_turn()
			else:
				board.erase_collision_cache(m.pos)
			
		self.remove_dead()
		
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
		
		for pos in board.iter_square(0, 0, width-1, height-1):
			tile = board.get_tile(pos)
			symbol = WALL_SYMBOL if tile.wall else " "
			self.draw_symbol(pos.y + offset_y, pos.x, symbol)
	
	def draw_stats(self):
		board = self.get_board()
		height = board.height
		width = board.width
		player = self.get_player()
		
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
			if m.state == "IDLE":
				color = curses.A_REVERSE
			self.draw_symbol(pos.y + offset_y, pos.x, "m", color)
		
		
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
		
	def draw_board(self):
		screen = self.screen
		offset_y = 0
		
		self.draw_walls(offset_y)
		self.draw_monsters(offset_y)
		self.draw_stats()
		self.draw_messages(offset_y)
		screen.move(20, 0)
		screen.refresh()
		
	