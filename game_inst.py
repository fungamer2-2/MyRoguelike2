from const import *
from items import *

from json_obj import *
from board import Board
from entity import Entity
from monster import Monster
from player import Player
from threading import Thread

from messages import MessageLog
from noise_event import NoiseEvent
from utils import *
from projectile import Projectile
	
import curses, textwrap, math, pickle, time

from inventory_ui import *

def _check_type(typ, types, type_name):
	if typ not in types:
		valid_types = sorted(types.keys())
		error = ValueError(f"invalid {type_name} type {typ!r}")
		error.add_note(f"Valid {type_name} types are: {', '.join(valid_types)}")
		raise error

class Game:
	_INST = None
	
	def __new__(cls):
		if cls._INST:
			return cls._INST
		obj = object.__new__(cls)
		cls._INST = obj
		return obj
	
	def __init__(self):
		self._board = Board(50, 18)
		self._player = Player()
		self.screen = None
		self.monsters = []
		self.msg_log = MessageLog(MESSAGE_LOG_CAPACITY)
		self.window_init = True
		self.mon_types = {}
		self.eff_types = {}
		self.weap_types = {}
		self.armor_types = {}
		self.level = 1
		self.subtick_timer = 0
		self.tick = 0
		self.select_mon = None
		self.noise_events = []
		self.revealed = set()
		self.delay = False
		self.last_save_turn = -999
		self.last_save_time = time.time()
		self.projectile = None
		
	def __getstate__(self):
		d = self.__dict__.copy()
		for field in ["screen", "mon_types", "eff_types", "weap_types", "armor_types"]:
			del d[field]
		return d
	
	def __setstate__(self, state):
		self.__dict__.update(state)
		
	def autosave(self):
		time_diff = time.time() - self.last_save_time
		if time_diff >= 2:
			self.last_save_time = time.time()
			t = Thread(target=self.save)
			t.start()
		
	def save(self):
		try:
			saved_data = pickle.dumps(self)	
		except:
			pass
		else:
			with open(SAVED_GAME_PATH, "wb") as file:
				file.write(saved_data)
			self.last_save_time = time.time()
			
	def load(self):
		obj = pickle.load(open(SAVED_GAME_PATH, "rb"))
		self.__dict__.update(obj.__dict__)
	
	def has_saved_game(self):
		import os
		return os.path.exists(SAVED_GAME_PATH)
		
	def delete_saved_game(self):
		if self.has_saved_game():
			import os
			os.remove(SAVED_GAME_PATH)
		
	def add_noise_event(self, pos, loudness, src=None):
		if loudness > 0:
			self.noise_events.append(NoiseEvent(pos, loudness, src))
		
	def set_mon_select(self, m):
		self.select_mon = m
	
	def clear_mon_select(self):
		self.select_mon = None
		
	def check_mon_type(self, typ):
		_check_type(typ, self.mon_types, "monster")
			
	def check_effect_type(self, name):
		_check_type(name, self.eff_types, "effect")
			
	def check_weapon_type(self, typ):
		_check_type(typ, self.weap_types, "weapon")
	
	def check_armor_type(self, typ):
		_check_type(typ, self.armor_types, "armor")
		
	def load_monsters(self):
		self.mon_types = load_monster_types()
	
	def load_effects(self):
		self.eff_types = load_effect_types()
		
	def load_weapons(self):
		self.weap_types = load_weapon_types()
		
	def load_armors(self):
		self.armor_types = load_armor_types()	
	
	def get_mon_type(self, typ):
		self.check_mon_type(typ)
		return self.mon_types[typ]
		
	def get_weapon_type(self, typ):
		self.check_weapon_type(typ)
		return self.weap_types[typ]
		
	def get_armor_type(self, typ):
		self.check_armor_type(typ)
		return self.armor_types[typ]
		
	def get_effect_type(self, name):
		self.check_effect_type(name)
		return self.eff_types[name]
		
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
		screen = curses.initscr()
		self.screen = screen	
		self.init_colors()
		
		curses.noecho()
		curses.curs_set(False)
		Entity.g = self
		screen.addstr("Loading game, please wait...")
		screen.refresh()
		
		self.load_json_data()
		
		if not self.check_saved_game():
			self.init_player()
			self.generate_level()
		
		
		
	def confirm_load_save(self):
		screen = self.screen
		screen.erase()
		screen.addstr(0, 0, "Continue Saved Game")
		
		screen.addstr(2, 0, "You have a saved game in progress. Would you like to load the saved game?")
		screen.addstr(3, 0, "(Press Y to load game, or N to start a new one)")
		screen.refresh()
		while True:
			char = chr(self.getch())
			
			if char.lower() == "y":
				self.load()
				return True
			elif char.lower() == "n":
				self.delete_saved_game()
				return False
		
	def check_saved_game(self):
		if self.has_saved_game():
			return self.confirm_load_save()
		else:
			return False
		
	def load_json_data(self):
		self.load_monsters()
		self.load_effects()
		self.load_weapons()
		self.load_armors()
		
	def next_level(self):
		player = self.get_player()
		
		self.level += 1
		
		if player.debug_wizard:
			self.level = self.input_int("As the wizard of debugging, you choose which level to go to. Which level number would you like to teleport to?")
		
		self.generate_level()
		self.refresh_mon_pos_cache()
		self.save()		
		self.draw_board()
		
	def generate_level(self):
		board = self.get_board()
		
		self.monsters.clear()
		self.revealed.clear()
		
		board.clear_los_cache()
		board.clear_collision_cache()
		board.procgen_level()
		self.place_player()
		self.place_monsters()
		self.place_items()
		
	def choose_mon_spawn_pos(self):
		board = self.get_board()
		player = self.get_player()
		force_outside_fov = x_in_y(3, 4) and x_in_y(8, self.level + 8)
		
		for tries in range(150):
			pos = board.random_pos()
			if board.passable(pos) and not self.entity_at(pos):
				if not (force_outside_fov and player.sees_pos(pos)):
					return pos
		
		return None
		
	def create_weapon(self, id):
		typ = self.get_weapon_type(id)
		return Weapon.from_type(typ)
		
	def create_armor(self, id):
		typ = self.get_armor_type(id)
		return Armor.from_type(typ)
	
	def place_items(self):
		board = self.get_board()
		
		potions = [
			[InvisibilityPotion, 25],
			[HealingPotion, 130],
			[EnlargementPotion, 20],
			[ShrinkingPotion, 20],
			[SpeedPotion, 30]
		]
		
		for _ in range(rng(1, 5)):
			pos = board.random_passable()
			
			typ = random_weighted(potions)
			board.place_item_at(pos, typ())
			
		weapons = [
			["club", 100],
			["dagger", 30],
			["greatclub", 70],
			["handaxe", 15],
			["battleaxe", 10],
			["scimitar", 6],
			["greatsword", 4],
			["greataxe", 5]
		]
		
		for _ in range(rng(1, 5)):
			if one_in(2):
				pos = board.random_passable()
				name = random_weighted(weapons)
				board.place_item_at(pos, self.create_weapon(name))
				
		armors = [
			["leather", 100],
			["hide", 100],
			["chain_shirt", 45],
			["scale_mail", 45],
			["half_plate", 10],
			["ring_mail", 27],
			["chain_mail", 18]
		]
		
		for _ in range(rng(2, 4)):
			if one_in(2):
				pos = board.random_passable()
				name = random_weighted(armors)
				board.place_item_at(pos, self.create_armor(name))
				
		scrolls = [
			[TeleportScroll, 20],
			[FogScroll, 20],
			[ThunderScroll, 20]
		]
		
		for _ in range(rng(1, 3)):
			if one_in(5):
				pos = board.random_passable()	
				typ = random_weighted(scrolls)
				board.place_item_at(pos, typ())
				
		if one_in(5):
			pos = board.random_passable()
			board.place_item_at(pos, Shield())
		
	def place_monsters(self):
		eligible_types = {}
		highest = 0
		
		special = not x_in_y(8, self.level) and one_in(6)
		
		levels = WeightedList()
		for typ in self.get_all_monster_types():
			if self.level >= typ.level:
				w = 3
				if typ.level > 1:
					w = min(w, self.level - typ.level + 1)
				if typ.level not in eligible_types:
					levels.add(typ.level, w)
					eligible_types[typ.level] = []
				eligible_types[typ.level].append(typ)
				
		assert len(eligible_types) > 0
			
		num_monsters = rng(5, 10)
		num_monsters += rng(0, round((self.level-1)**(2/3)))
		
		packs = 0
		while num_monsters > 0:
			typ = random.choice(eligible_types[levels.pick()])
			min_level = typ.level
			if "PACK_TRAVEL" in typ.flags and x_in_y(self.level, self.level + 6) and one_in(6 + packs * 3):
				pack_num = rng(3, 5)
				if self.spawn_pack(typ.id, pack_num):
					num_monsters -= pack_num
					packs += 1	
			else:
				num_monsters -= 1
				self.place_monster(typ.id)
		
	def spawn_pack(self, typ, num):
		self.check_mon_type(typ)
		board = self.get_board()
		
		pos = self.choose_mon_spawn_pos()
		
		if not pos:
			return False
		
		candidates = []
		for p in board.points_in_radius(pos, 6):
			if not board.passable(p):
				continue
			if self.entity_at(p):
				continue	
			if one_in(2) or board.has_line_of_sight(p, pos):
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
	
	def init_player(self):
		player = self.get_player()	
		self.place_player()
		player.recalc_max_hp()
		
	def place_player(self):
		board = self.get_board()
		player = self.get_player()
		while True:
			pos = board.random_passable()
			for p in board.points_in_radius(pos, 1):
				if p != pos and player.can_move_to(p):	
					player.move_to(pos)
					board.set_collision_cache(pos, player)
					return
					
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
		
		pos = self.choose_mon_spawn_pos()
		if not pos:
			return None
			
		return self.place_monster_at(typ_id, pos)
	
	def entity_at(self, pos):
		board = self.get_board()
		return board.get_collision_cache(pos)
		
	def monster_at(self, pos):
		entity = self.entity_at(pos)
		if entity and entity.is_monster():
			return entity
		return None
		
	def monsters_in_radius(self, pos, radius):
		board = self.get_board()
		for pos in board.points_in_radius(pos, radius):
			if (mon := self.monster_at(pos)):
				yield mon
				
	def once_every_num_turns(self, num):
		return self.tick % num == 0
			
	def get_board(self):
		return self._board
		
	def get_player(self):
		return self._player
		
	def get_monsters(self):
		return [mon for mon in self.monsters if mon.is_alive()]	
	
	def process_noise_events(self):
		if not self.noise_events:
			return
		for noise in self.noise_events:
			for m in self.monsters:
				if not (noise.src and noise.src is m):
					m.on_hear_noise(noise)
			player = self.get_player()
			player.on_hear_noise(noise)	
		self.noise_events.clear()
			
	def do_turn(self):
		board = self.get_board()
		player = self.get_player()
		used = player.energy_used
		
		
		if used <= 0:
			return
			
		self.autosave()
		
		board.tick_fields(used)	
			
		while player.energy_used > 0:
			amount = min(player.energy_used, 100)		
			player.do_turn(amount)
		
		self.subtick_timer += used
		player.energy += used
		for m in self.monsters:		
			m.energy += used	
		
		self.process_noise_events()	
		
		while self.subtick_timer >= 100:
			self.subtick_timer -= 100
			self.tick += 1
			player.tick()
			for m in self.monsters:
				if m.is_alive():
					m.tick()
					
		
		remaining = self.monsters.copy()
		random.shuffle(remaining)
		remaining.sort(key=lambda m: m.energy, reverse=True)
		
		self.refresh_mon_pos_cache()
		
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
		self.process_noise_events()
		
	def items_at(self, pos):
		board = self.get_board()
		return board.get_tile(pos).items	
			
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
		
		for _ in range(5):
			pos = board.random_passable()
			if not self.items_at(pos):
				break
		
		tile = board.get_tile(pos)
		tile.stair = 1
			
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
				
			seen = player.sees_pos(pos)
			color = 0 if seen else curses.color_pair(COLOR_GRAY)
				
			if tile.wall:
				symbol = WALL_SYMBOL
			elif seen and board.field_at(pos):
				symbol = "8"
				color = curses.color_pair(COLOR_SILVER) | curses.A_REVERSE
				
			elif seen and tile.items:
				item = tile.items[-1]
				symbol = item.symbol
				color = item.display_color()
			elif tile.stair:
				symbol = STAIR_SYMBOL
			else:
				symbol = "." if seen else " "
				if seen:
					color = curses.color_pair(COLOR_GRAY)
			
			self.draw_symbol(pos.y + offset_y, pos.x, symbol, color)
	
	def maybe_draw_projectile(self, offset_y):
		if not self.projectile:
			return
		player = self.get_player()
		proj = self.projectile
		
		if player.sees_pos(proj):
			self.draw_symbol(proj.y + offset_y, proj.x, "*")
	
		
	def draw_stats(self):
		board = self.get_board()
		height = board.height
		width = board.width
		player = self.get_player()
		
		bar = "HP: " + display_bar(player.HP, player.MAX_HP, 20)			
		p = f"({player.HP}/{player.MAX_HP})"
		bar += " " + p
		
		if player.HP <= player.MAX_HP // 4:
			color = COLOR_RED
		elif player.HP <= player.MAX_HP // 2:
			color = COLOR_YELLOW
		else:
			color = COLOR_GREEN
			
		self.draw_string(0, 0, bar, curses.color_pair(color))
		
		xp_needed = player.xp_to_next_level()
		xp_curr = player.xp
		
		xp_str = f"XP Level: {player.xp_level} - {xp_curr}/{xp_needed} | Depth: {self.level}"
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
		
		offset = len(strings) + 1
		ev = player.calc_evasion() - 10
		ev = round(ev, 1)
		stealth = round(player.stealth_mod(), 1)
		
		ev_str = f"+{ev}" if ev >= 0 else str(ev)
		
		stealth_str = f"+{stealth}" if stealth >= 0 else str(stealth)
		
		wield_str = player.weapon.name
		dmg_str = str(player.weapon.damage)
		
		armor_str = player.armor.name if player.armor else ""
		prot_str = f"Protection: {player.get_armor()}"
		strings2 = [
			f"Stealth: {stealth_str}",
			f"Evasion: {ev_str}",
			f"Wield: {wield_str}",
			f"Damage: {dmg_str}",
			armor_str,
			prot_str,
			"Using Shield" if player.shield else ""
		]
		
		for i, string in enumerate(strings2):
			self.draw_string(i + offset, width + 6, string)
			
		offset += len(strings2) + 1
		status = sorted(list(player.get_all_status_effects()))
		if status:
			for i, string in enumerate(status):
				eff = self.get_effect_type(string)
				color = curses.color_pair(MSG_TYPES[eff.type])
				
				self.draw_string(i + offset, width + 6, string, color)
				
				if i >= 12:
					break
					
	def draw_monsters(self, offset_y):
		player = self.get_player()
		for m in player.visible_monsters():
			pos = m.pos
			symbol = m.symbol 
			
			color = m.display_color()
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
		rows, _ = screen.getmaxyx()
		cols = board.width + 4
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
		
		board = self.get_board()
		player = self.get_player()
		
		if board.recalc_sight:
			player.calc_fov()
			board.recalc_sight = False
		
		self.reveal_seen_tiles()
		self.draw_walls(offset_y)
		self.draw_monsters(offset_y)
		self.maybe_draw_projectile(offset_y)
		self.draw_stats()
		self.draw_messages(offset_y+1)
		screen.move(20 + offset_y, 0)
		screen.refresh()
		
	def maybe_refresh(self):
		player = self.get_player()
		
		if not player.is_resting or self.once_every_num_turns(5):
			self.draw_board()
			
	def input_text(self, msg=""):
		curses.curs_set(True)
		curses.echo()
		screen = self.screen
		
		if msg:
			self.add_message(msg, "input")
		self.draw_board()
		screen.move(20, 0)
		result = screen.getstr()
		curses.curs_set(False)
		curses.noecho()
		return result.decode().rstrip()
		
	def input_int(self, msg=""):
		while True:
			txt = self.input_text(msg)
			try:
				return int(txt)
			except ValueError:
				self.add_message("Integers only, please.", "input")
	
	def confirm(self, question):
		while True:
			txt = self.input_text(question + " (Y/N)")
			if txt in ["Y", "N"]:
				return txt == "Y"
			else:
				self.add_message("Please enter an uppercase Y or N.", "input")		
	
	def process_input(self):	
		self.maybe_refresh()
				
		player = self.get_player()
		board = self.get_board()
		
		if player.is_resting:
			if player.HP >= player.MAX_HP:
				self.add_message("HP restored.", "good")
				player.is_resting = False
				self.save()
			else:
				player.use_energy(100)
			return True
			
		if player.has_status("Paralyzed"):
			player.use_energy(100)
			return True
			
		player.handle_activities()
		if player.activity:
			player.use_energy(100)
			return True
		
		self.draw_board()
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
			if player.can_rest():
				self.add_message("You begin resting.")
				player.is_resting = True
			return True
		elif char == "v":
			return self.view_monsters()
		elif char == "p":
			return player.pickup()
		elif char == "u":
			self.add_message("The 'u'se menu has been moved to the 'i'nventory menu.", "info")
		elif char == "i":
			return self.open_player_inventory()
		elif char == " ":
			player.use_energy(100)
			return True
		elif char == "Q":
			if self.confirm("Are you sure to want to close the game? (Your game will be saved so you can come back to it later.)"):
				self.save()
				self.deinit_window()
				exit()
			
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
		
		cursor = 0
		mon = None
		
		min_dist = 999
		nearest = None
		for i, m in enumerate(monsters):
			dist = player.distance(m)
			if dist < min_dist:
				min_dist = dist
				nearest = m
				cursor = i
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
		info.add_line(f"{monster.symbol} - {monster.name} ({monster.HP}/{monster.MAX_HP} HP)")
		info.add_line()
		stats_str = f"STR {monster.STR}, DEX {monster.DEX}, CON {monster.CON}"
		info.add_line(stats_str)
		info.add_line()
		if monster.state == "IDLE":
			info.add_line("It hasn't noticed your presence yet.")
		if monster.has_flag("PACK_TRAVEL"):
			info.add_line("This creature may travel in packs.")
		if monster.has_flag("PACK_TACTICS"):
			info.add_line("This creature takes advantage of its nearby allies to attack targets more easily.")	
		
		blindsight = monster.type.blindsight_range
		if blindsight > 0:
			string = f"This creature has blindsight to a radius of {blindsight} tiles"
			if not monster.can_see():
				string += " (blind beyond this range)"
			string += "."
			info.add_line(string)
		mon_speed = monster.get_speed()
		player_speed = player.get_speed()
		diff = mon_speed / player_speed
		
		if mon_speed != player_speed:
			if mon_speed > player_speed:
				diff_str = f"{diff:.2f}x"
			else:
				diff_str = f"{diff*100:.1f}%"
			info.add_line(f"This monster is about {diff_str} as fast as you.")	
		 
		mon_ev = monster.calc_evasion()	
		player_ev = player.calc_evasion()
		
		#If using a shield, factor that into the calculation
		if player.shield:
			player_ev += SHIELD_BONUS
		
		player_to_hit = gauss_roll_prob(player.calc_to_hit_bonus(monster), mon_ev)
		monster_to_hit = gauss_roll_prob(monster.calc_to_hit_bonus(player), player_ev)
		
		player_to_hit = player_to_hit*(1-MIN_HIT_MISS_PROB/100) + MIN_HIT_MISS_PROB/2
		monster_to_hit = monster_to_hit*(1-MIN_HIT_MISS_PROB/100) + MIN_HIT_MISS_PROB/2
		
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
		self.delete_saved_game()
		self.draw_board()
		self.draw_game_over()
		self.screen.refresh()
		while self.getch() != 10: 
			pass
			
	def open_player_inventory(self):
		player = self.get_player()
		
		if not player.inventory:
			self.add_message("Your inventory is empty.")
			return False
		
		return inventory_menu(self)
		
				
	def do_projectile(self, pos1, pos2):
		board = self.get_board()
		player = self.get_player()
		
		path_iter = board.find_clear_path_to(pos1, pos2)
		try:
			for pos in path_iter:
				if pos == pos1:
					continue
				self.projectile = pos
				yield pos
				if player.sees_pos(pos):
					self.draw_board()
					time.sleep(ANIMATION_DELAY)
		except GeneratorExit:
			pass
		self.projectile = None
		
class PopupInfo:
	
	def __init__(self, g):
		self.g = g
		screen = g.screen
		self.screen = screen.subwin(18, 50, 2, 0)
		self.lines = []
		self.scroll = 0
		
	def set_scroll(self, num):
		screen = self.screen
		h, w = screen.getmaxyx()
		max_disp = h - 2
		max_scroll = max(0, len(self.lines) - max_disp)
		self.scroll = clamp(self.scroll, 0, max_scroll)
		
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
			ind = i + self.scroll
			screen.addstr(i + 1, 1, self.lines[ind])
		
		screen.refresh()