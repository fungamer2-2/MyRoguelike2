from json_obj import load_monster_types
from board import Board
from entity import Entity
from monster import Monster
from player import Player
from const import *
from messages import MessageLog

from utils import *	
import curses, textwrap, math

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
		self.subtick_timer = 0
		self.tick = 0
		self.select_mon = None
		
	def set_mon_select(self, m):
		self.select_mon = m
	
	def clear_mon_select(self):
		self.select_mon = None
		
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
		
	def add_message(self, text, typ="neutral"):
		self.msg_log.add_message(text, typ)
		
	def init_colors(self):
		curses.start_color()
		assert curses.has_colors()
		
		curses.use_default_colors()
		for i in range(curses.COLORS-1):
			curses.init_pair(i + 1, i + 1, -1)
		
	def init_game(self):
		self.screen = curses.initscr()
		
		self.init_colors()
		
		curses.noecho()
		curses.curs_set(False)
		Entity.g = self
		self.load_monsters()
		
		self.generate_level()		
		self.draw_board()
		
	def next_level(self):
		self.level += 1
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
			
		num_monsters = rng(5, 10)
		num_monsters += rng(0, round((self.level-1)**(2/3)))
		
		packs = 0
		while num_monsters > 0:
			typ = random.choice(eligible_types)
			if typ.pack_travel and x_in_y(self.level, self.level + 2) and one_in(6 + packs * 2):
				pack_num = rng(2, 4)
				if self.spawn_pack(typ.id, pack_num):
					num_monsters -= rng(1, pack_num)
					packs += 1	
			else:
				num_monsters -= 1
				self.place_monster(typ.id)
		
	def spawn_pack(self, typ, num):
		self.check_mon_type(typ)
		board = self.get_board()
		for tries in range(75):
			pos = board.random_pos()
			if board.passable(pos) and not self.entity_at(pos):
				break
		
		candidates = []
		for p in board.points_in_radius(pos, 4):
			if not board.passable(p):
				continue
			if self.entity_at(p):
				continue	
			if board.has_line_of_sight(p, pos):
				candidates.append(p)
		if not candidates:
			return False
			
		random.shuffle(candidates)
		candidates.sort(key=lambda p: p.distance(pos))
		
		num = min(len(candidates), num)
		for i in range(num):
			self.place_monster_at(typ, candidates[i])
		
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
			
		for tries in range(150):
			pos = board.random_pos()
			if board.passable(pos) and not self.monster_at(pos):
				break
			
		
		return self.place_monster_at(typ_id, pos)
		
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
				
	def once_every_num_turns(self, num):
		return self.tick % num == 0
			
	def get_board(self):
		return self._board
		
	def get_player(self):
		return self._player
		
	def get_monsters(self):
		return [mon for mon in self.monsters if mon.is_alive()]	
		
	def do_turn(self):
		board = self.get_board()
		player = self.get_player()
		used = player.energy_used
		
		if used <= 0:
			return
		self.refresh_mon_pos_cache()
		player.do_turn()
		
		self.subtick_timer += used
		player.energy += used	
		for m in self.monsters:		
			m.energy += used
			
		while self.subtick_timer >= 100:
			self.subtick_timer -= 100
			self.tick += 1
			for m in self.monsters:
				m.tick()
			
		remaining = self.monsters.copy()
		
		while len(remaining) > 0:
			nextremain = []
			for m in remaining:
				if not m.is_alive():
					continue
				if m.energy <= 0:
					continue
				m.do_turn()
				if m.energy > 0:
					nextremain.append(m)
			remaining = nextremain
		
		self.remove_dead()	
			
	def refresh_mon_pos_cache(self):
		board = self.get_board()
		player = self.get_player()
		board.clear_collision_cache()
		
		board.set_collision_cache(player.pos, player)	
		for m in self.monsters:
			if m.is_alive():
				board.set_collision_cache(m.pos, m)
		
	def remove_dead(self):
		for m in reversed(self.monsters):
			if not m.is_alive():
				self.monsters.remove(m)
				
	def place_stairs(self):
		board = self.get_board()
		while True:
			pos = board.random_pos()
			if board.passable(pos):
				tile = board.get_tile(pos)
				tile.stair = True
				return
			
	def getch(self, wait=True):
		screen = self.screen
		screen.nodelay(not wait)
		if wait:
			curses.flushinp()
			
		code = screen.getch()
		return code
	
	def draw_symbol(self, row, col, symbol, color=0):
		screen = self.screen
		rows, cols = screen.getmaxyx()
		
		if 0 <= row < rows and 0 <= col < cols:
			screen.addstr(row, col, symbol, color)
		
	def draw_string(self, row, col, string, color=0):
		screen = self.screen
		rows, cols = screen.getmaxyx() 
		if col >= cols or not (0 <= row < rows):
			return
		diff = cols - (col + len(string))
		if diff < 0:
			string = string[:diff]
		screen.addstr(row, col, string, color)	 
		
	def draw_walls(self, offset_y):	
		board = self.get_board()
		player = self.get_player()
		height = board.height
		width = board.width
		player = self.get_player()
		
		for pos in board.iter_square(0, 0, width-1, height-1):
			tile = board.get_tile(pos)
			if not tile.revealed:
				continue
				
			if tile.wall:
				symbol = WALL_SYMBOL
			elif tile.stair:
				symbol = STAIR_SYMBOL
			else:
				symbol = "." if player.sees(pos) else " "
			
			self.draw_symbol(pos.y + offset_y, pos.x, symbol)
			
	def draw_stats(self):
		board = self.get_board()
		height = board.height
		width = board.width
		player = self.get_player()
		
		bar = "HP: " + display_bar(player.HP, player.MAX_HP, 20)			
		p = f"({player.HP}/{player.MAX_HP})"
		bar += " " + p
		
		if player.HP <= player.MAX_HP // 5:
			color = COLOR_RED
		elif player.HP <= player.MAX_HP // 2:
			color = COLOR_YELLOW
		else:
			color = COLOR_GREEN
			
		self.draw_string(0, 0, bar, curses.color_pair(color))
		
		xp_needed = player.xp_to_next_level()
		xp_curr = player.xp
		
		xp_str = f"XP Level: {player.xp_level} - {xp_curr}/{xp_needed}"
		self.draw_string(1, 0, xp_str)
		
		
		strings = [
			f"STR {player.STR}",
			f"DEX {player.DEX}",
			f"CON {player.CON}",
			f"INT {player.INT}",
			f"WIS {player.WIS}",
			f"CHA {player.CHA}"
		]
		for i, string in enumerate(strings):
			self.draw_string(i, width + 6, string)	

	def draw_monsters(self, offset_y):
		player = self.get_player()
		for m in self.monsters:
			pos = m.pos
			color = 0
			
			if not player.sees(m):
				continue
			symbol = m.symbol 
			if m.state == "IDLE":
				color = curses.A_REVERSE
			if m is self.select_mon:
				color = curses.color_pair(COLOR_GREEN) | curses.A_REVERSE
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
		for message, type in reversed(messages):
			msg_lines = textwrap.wrap(message, width=cols)
			groups.append([(line, type) for line in msg_lines])
			total_lines += len(msg_lines)
			if total_lines >= 8:
				break
		groups.reverse()
		
		displayed = []
		for group in groups:
			displayed.extend(group)
		displayed = displayed[-8:] 
			
		for i in range(len(displayed)):
			msg, type = displayed[i]
			color = curses.color_pair(MSG_TYPES[type])
			self.draw_string(y + i, 0, msg, color)			

	def reveal_seen_tiles(self):
		board = self.get_board()
		player = self.get_player()
		for pos in player.fov:
			board.reveal_tile_at(pos)
			
	def draw_board(self):
		screen = self.screen
		screen.erase()
		offset_y = 2
		
		self.reveal_seen_tiles()
		self.draw_walls(offset_y)
		self.draw_monsters(offset_y)
		self.draw_stats()
		self.draw_messages(offset_y)
		screen.move(20 + offset_y, 0)
		screen.refresh()
		
	def maybe_refresh(self):
		player = self.get_player()
		
		if not player.is_resting or self.once_every_num_turns(5):
			self.draw_board()
	
	def process_input(self):
		self.maybe_refresh()
				
		player = self.get_player()
		
		if player.is_resting:
			if player.HP >= player.MAX_HP:
				self.add_message("HP restored.", "good")
				player.is_resting = False
			else:
				player.use_energy(100)
			return True
		
		code = self.getch()
		char = chr(code)
		
		if char == "w":
			return player.move_dir(0, -1)
		if char == "s":
			return player.move_dir(0, 1)
		elif char == "a":
			return player.move_dir(-1, 0)
		elif char == "d":
			return player.move_dir(1, 0)
		elif char == ">":
			return player.descend()
		elif char == "r":
			if player.HP < player.MAX_HP:
				self.add_message("You begin resting.")
				player.is_resting = True
				return True
		elif char == "v":
			return self.view_monsters()
		elif char == " ":
			player.use_energy(100)
			return True
		
		return False
		
	def select_monster_menu(self, monsters, check_fov=True):
		player = self.get_player()
		monsters = monsters.copy()
		
		if check_fov:
			monsters = [mon for mon in monsters if player.sees(monster)]
		if not monsters:
			return False
			
		#Sort by y position first, then sort by x position
		monsters.sort(key=lambda m: m.pos.y)
		monsters.sort(key=lambda m: m.pos.x)
		
		self.add_message("View info of which monster? (Use the a and d keys to select, then press Enter)")
		
		cursor = (len(monsters)-1)//2
		mon = None
		while True:
			self.set_mon_select(monsters[cursor])
			self.draw_board()
			code = self.getch()
			char = chr(code)
			if char == "a":
				cursor -= 1
			elif char == "d":
				cursor += 1
			elif code == 10:
				mon = monsters[cursor]
				break
			cursor %= len(monsters)
		
		self.clear_mon_select()
		self.print_monster_info(mon)	
		return False
		
	def print_monster_info(self, monster):
		player = self.get_player()
		
		a_an = "an" if monster.name[0] in "aeiou" else "a"
		
		info = PopupInfo(self)
		info.add_line(f"{monster.symbol} - {monster.name}")
		info.add_line()
		if monster.state == "IDLE":
			info.add_line("It hasn't noticed your presence yet.")
		if monster.pack:
			info.add_line("This creature travels in packs and takes advantage of its nearby allies to attack targets more easily.")
		
		mon_speed = monster.get_speed()
		player_speed = player.get_speed()
		diff = mon_speed / player_speed
		
		if mon_speed != player_speed:
			if mon_speed > player_speed:
				diff_str = f"{diff:.2f}x"
			else:
				diff_str = f"{diff*100:.2f}%"
			info.add_line(f"This monster is about {diff_str} as fast as you.")	
		 
		
		player_to_hit = gauss_roll_prob(player.calc_to_hit_bonus(monster), monster.calc_evasion())
		monster_to_hit = gauss_roll_prob(monster.get_to_hit_bonus(), player.calc_evasion())
		
		info.add_line(f"Your attacks have a {player_to_hit:.1f}% probability to hit this creature.")
		info.add_line(f"Its attacks have a {monster_to_hit:.1f}% probability to hit you.")
		info.show()
		self.getch()
		
	def view_monsters(self):
		player = self.get_player()
		monsters = list(player.visible_monsters())
		return self.select_monster_menu(monsters, False)
	
	def create_popup_window(self):
		screen = self.screen
		win = screen.subwin(18, 50, 2, 0)
		win.erase()
		win.border("|", "|", "-", "-", "+", "+", "+", "+")
		return win
		
	def draw_game_over(self):
		gameover_win = self.create_popup_window()
		
		def draw_center_text(y, txt):
			h, w = gameover_win.getmaxyx()
			x = (w - len(txt))//2			
			gameover_win.addstr(y, x, txt)
		
		draw_center_text(1, "GAME OVER")
		draw_center_text(2, "You have died.")
		draw_center_text(4, "Press Enter to exit.")
		gameover_win.refresh()
		
	def game_over(self):
		self.draw_board()
		self.draw_game_over()
		self.screen.refresh()
		while self.getch() != 10: 
			pass
		
class PopupInfo:
	
	def __init__(self, g):
		self.g = g
		screen = g.screen
		self.screen = screen.subwin(18, 50, 2, 0)
		self.lines = []
		
	def add_line(self, line=None):
		screen = self.screen
		h, w = screen.getmaxyx()
		max_width = w - 2
		
		if line is None:
			self.lines.append("")
		else:
			lines = textwrap.wrap(line, width=max_width)	
			self.lines.extend(lines)
		
	def show(self):
		screen = self.screen
		screen.erase()
		screen.border("|", "|", "-", "-", "+", "+", "+", "+")
		h, w = screen.getmaxyx()
		
		max_disp = h - 2
		
		for i in range(min(len(self.lines), max_disp)):
			screen.addstr(i + 1, 1, self.lines[i])
		
		screen.refresh()