from entity import Entity
from utils import *
from const import *
from items import UNARMED

class Player(Entity):
	
	def __init__(self):
		super().__init__()
		stats = gen_stats()
		self.STR = stats[0] + 1
		self.DEX = stats[1] + 1
		self.CON = stats[2] + 1
		self.INT = stats[3] + 1
		self.WIS = stats[4] + 1
		self.CHA = stats[5] + 1
		self.MAX_HP = 10
		self.xp = 0
		self.xp_level = 1
		self.regen_tick = 0
		self.fov = set()
		self.energy_used = 0
		self.is_resting = False
		self.debug_wizard = False
		self.weapon = UNARMED
		self.inventory = []
		
	def is_unarmed(self):
		return self.weapon is UNARMED
		
	def calc_evasion(self):
		bonus = 5 + stat_mod(self.DEX)
		if not self.is_alive():
			bonus = 0
		else:
			if self.has_status("Hasted"):
				bonus += 2
			if self.has_status("Enlarged"):
				bonus *= 0.7
			elif self.has_status("Reduced"):
				bonus *= 1.3
		return bonus + 5
		
	def add_to_inventory(self, item):
		self.inventory.append(item)
		
	def interrupt(self):
		self.is_resting = False
		
	def use_energy(self, amount):
		super().use_energy(amount)
		self.energy_used += amount
		
	def is_player(self):
		return True
		
	def xp_to_next_level(self):
		amount = 100 * self.xp_level ** 1.5
		return round(amount/10)*10
		
	def gain_xp(self, amount):
		self.xp += amount
		old_level = self.xp_level
		num = 0
		while self.xp >= self.xp_to_next_level():
			self.xp -= self.xp_to_next_level()
			self.xp_level += 1
			self.recalc_max_hp()
				
			if self.xp_level % 3 == 0:
				num += 1
				
				
		if old_level != self.xp_level:
			
			self.add_msg(f"You have reached experience level {self.xp_level}!", "good")
			for _ in range(num*2):
				rand = rng(1, 6)
				match rand:
					case 1:
						self.STR += 1
						msg = "You feel stronger."
					case 2:
						self.DEX += 1
						msg = "You feel more agile."
					case 3:
						self.CON += 1
						self.recalc_max_hp()
						msg = "You feel your physical endurance improve."
					case 4:
						self.INT += 1
						msg = "You feel more intelligent."
					case 5:
						self.WIS += 1
						msg = "You feel wiser."
					case 6:
						self.CHA += 1
						msg = "You feel more charismatic."
			
				self.add_msg(msg, "good")
				
	def calc_fov(self):
		g = self.g
		board = g.get_board()
		self.fov = board.get_fov(self.pos)
		
	def sees_pos(self, other):
		return other in self.fov
	
	def sees(self, other):
		if self is other:
			return True
		
		return self.sees_pos(other.pos)
		
	def visible_monsters(self):
		g = self.g
		for m in g.monsters:
			if self.sees(m):
				yield m
				
	def maybe_alert_monsters(self, chance):
		for mon in self.visible_monsters():
			if x_in_y(chance, 100):
				mon.alerted()
					
	def speed_mult(self):
		mult = super().speed_mult()
		if self.has_status("Hasted"):
			mult *= 2
		return mult
		
	def get_name(self, capitalize=False):
		return "You" if capitalize else "you"
		
	def calc_to_hit_bonus(self, mon):
		level_bonus = (self.xp_level - 1) / 3
		stat = (self.STR + self.DEX) / 2
		if self.weapon.finesse:
			stat = max(self.STR, self.DEX) * 1.1
		
		stat_bonus = stat_mod(stat)
		mod = level_bonus + stat_bonus
		if not mon.is_aware():
			mod += 5
		
		if self.has_status("Reduced"):
			mod += 1.5
			
		if self.is_unarmed():
			mod += 1
		return mod
		
	def regen_rate(self):
		mult = self.CON / 10
		return 0.035 * mult
		
	def recalc_max_hp(self):
		base_hp = 10
		mult = base_hp * 0.75
		level_mod = mult * (self.xp_level - 1)
		level_mod *= self.CON / 10
		level_mod = max(level_mod, 2 * (self.xp_level - 1))
		val = base_hp + level_mod
		if self.has_status("Enlarged"):
			val *= 1.5
		elif self.has_status("Reduced"):
			val *= 0.7
			
		oldhp = self.MAX_HP
		newhp = round(val)
		
		self.MAX_HP = newhp
		
		if self.MAX_HP != oldhp:
			scale = self.MAX_HP / oldhp
			self.HP = max(1, math.ceil(scale * self.HP))
		
	def move_to(self, pos):
		if super().move_to(pos):
			self.fov.clear()
			self.calc_fov()
			return True
		return False
		
	def pickup(self):
		g = self.g
		board = g.get_board()
		items = g.items_at(self.pos)
		if not items:
			self.add_msg("There's nothing to pick up there.")
			return False
			
		item = items.pop()
		self.add_msg(f"You pick up a {item.name}.")
		self.add_to_inventory(item)
		self.use_energy(100)
		return True
		
	def use_item(self):
		if not self.inventory:
			self.add_msg("You have nothing in your inventory.")
			return False
		g = self.g
		item = g.select_use_item()
		if not item:
			return False
		used = item.use(self)
		if used:
			self.inventory.remove(item)
		return used	
		
	def on_move(self, oldpos):
		g = self.g
		prev_dist = [(mon, oldpos.distance(mon.pos)) for mon in self.visible_monsters()]
		
		items = g.items_at(self.pos)
		if items:
			if len(items) == 1:
				item = items[0]
				self.add_msg(f"You see a {item.name} here.")
			else:
				items = ", ".join(item.name for item in items)
				self.add_msg(f"You see here: {items}")
		for mon, old_dist in prev_dist:
			if not mon.is_aware():
				continue
			reach = mon.reach_dist() 
			if reach > 1 and not mon.has_clear_path_to(self.pos):
				continue
			
			if old_dist <= reach and self.distance(mon) > reach and mon.sees(self):
				player_roll = triangular_roll(0, self.get_speed())
				monster_roll = triangular_roll(0, mon.get_speed())
				if monster_roll >= player_roll and one_in(2):
					self.add_msg(f"{mon.get_name(True)} makes an opportunity attack as you move away!", "warning")
					oldenergy = mon.energy
					mon.attack_pos(self.pos)
					mon.energy = oldenergy
					
	def descend(self):
		g = self.g
		board = g.get_board()
		tile = board.get_tile(self.pos)
		if not tile.stair:
			self.add_msg("You can't go down there.")
			return False
		
		self.add_msg("You descend the stairs to the next level.")
		g.next_level()
		return True
		
	def take_damage(self, dam):
		if dam > 0:
			self.set_hp(self.HP - dam)
			self.interrupt()
			if 0 < self.HP <= self.MAX_HP // 5:
				self.add_msg(f"***LOW HP WARNING***", "bad")
			if self.HP <= 0:
				if self.debug_wizard:
					self.add_msg("You can't die while you're debugging, can you?", "good")
					self.heal(999)
				else:
					self.add_msg("You have died...", "bad")			
	
	def combat_noise(self, damage, sneak_attack):
		weapon = self.weapon
		match weapon.dmg_type:
			case "bludgeon":
				scale = 6
			case "pierce":
				scale = 2
			case _:
				scale = 4
		
		noise = rng(1, 2) + mult_rand_frac(round(damage ** 0.6), scale, 5)
		
		
		if sneak_attack:
			noise = div_rand(noise, 3)
			
		if noise > 0:
			self.make_noise(noise)
			
	def base_damage_roll(self):
		return self.weapon.roll_damage()
	
	def attack_pos(self, pos):
		g = self.g
		if (mon := g.monster_at(pos)) is None:
			self.add_msg("You swing at empty space.")
			self.use_energy(100)
			return True
		
		sneak_attack = False
		mod = self.calc_to_hit_bonus(mon)
		if not mon.is_aware():
			if x_in_y(self.DEX, 60):
				sneak_attack = True
		
		roll = gauss_roll(mod)
		evasion = mon.calc_evasion()
		margin = roll - evasion
		
		if x_in_y(MIN_HIT_MISS_PROB, 100):
			margin = 1000 if one_in(2) else -1000
		
		if margin >= 0:	
			damage = self.base_damage_roll() + div_rand(self.STR - 10, 2)
			crit = False
			if margin >= 5:
				crit = one_in(10)
			
			if sneak_attack:
				eff_level = self.xp_level
				if self.weapon.finesse:
					eff_level = mult_rand_frac(eff_level, 4, 3)
					eff_level += rng(0, 3)
				msg = [
					f"You catch {mon.get_name()} off-guard!",
					f"You strike {mon.get_name()} while it was unaware!",
					f"You sneak up and strike {mon.get_name()} from behind!"
				]
				self.add_msg(random.choice(msg))
				max_bonus = 3 + mult_rand_frac(eff_level, 3, 2)
				damage += dice(1, 2 + eff_level * 2)
				
				mon.use_energy(triangular_roll(0, 100))
				
			if self.has_status("Enlarged"):
				damage += dice(1, 6)
			elif self.has_status("Reduced"):
				damage = (damage + 1) // 2
		
			armor = mon.get_armor()
			if crit:
				damage += self.base_damage_roll()
				armor = div_rand(armor, 2)
			
			damage = max(damage, 1)
			damage = apply_armor(damage, armor)	
			
			self.combat_noise(damage, sneak_attack)
			
			self.add_msg(f"You hit {mon.get_name()} for {damage} damage.")
			if crit:
				self.add_msg("Critical hit!", "good")
			mon.take_damage(damage)
			if mon.is_alive():
				self.add_msg(f"It has {mon.HP}/{mon.MAX_HP} HP.")
			else:
				self.on_defeat_monster(mon)
		else:
			self.add_msg(f"Your attack misses {mon.get_name()}.")
			
		attack_cost = 100
		if self.has_status("Hasted"):
			attack_cost = 75
		self.use_energy(attack_cost)
		
		mon.alerted()
		self.maybe_alert_monsters(15)
		return True
		
	def on_defeat_monster(self, mon):
		g = self.g
		xp_gain = 15 * mon.get_diff_level()**1.5
		xp_gain = round(xp_gain/5)*5
		self.gain_xp(xp_gain)
		
		if len(g.get_monsters()) <= 0:
			g.place_stairs()
			self.add_msg("The stairs proceeding downward to the next level begin to open up...")
			if g.level == 1:
				self.add_msg("You have completed the first level! Move onto the '>', then press the '>' key to go downstairs.", "info")
			
	def move_dir(self, dx, dy):
		oldpos = self.pos.copy()
		if super().move_dir(dx, dy):
			self.use_energy(div_rand(10000, self.get_speed()))
			self.on_move(oldpos)	
			return True
		g = self.g
		pos = self.pos	
		target = Point(pos.x + dx, pos.y + dy)
		if g.monster_at(target):
			return self.attack_pos(target)
				
		return False
	
	def add_status(self, name, dur, silent=False):
		g = self.g
		eff_type = g.get_effect_type(name)
		if not silent:
			if self.has_status(name):
				msg_type = "info"
				if eff_type.type == "bad":
					msg_type = "bad"
				self.add_msg(eff_type.extend_msg, msg_type)	
			else:
				self.add_msg(eff_type.apply_msg, eff_type.type)
		super().add_status(name, dur)
		
	def tick_poison(self, subt):
		if self.poison > 0:
			amount = 1 + div_rand(self.poison, 12)
			dmg = mult_rand_frac(amount, subt, 100)
			dmg = min(dmg, self.poison)
			self.take_damage(dmg)	
			self.poison -= dmg
			if self.poison < 0:
				self.poison = 0
			if dmg > 0 and (one_in(4) or x_in_y(self.poison, self.MAX_HP)):
				self.add_msg("You feel sick due to the poison in your system.", "bad")
	
	def do_turn(self, used):
		g = self.g
		
		subt = used / 100
		self.energy_used -= used
		self.regen_tick += self.regen_rate() * subt
		while self.regen_tick >= 1:
			self.regen_tick -= 1
			self.heal(1)
			
		self.tick_poison(used)
		
		for name in list(self.status.keys()):
			self.status[name] -= used
			if self.status[name] <= 0:
				self.remove_status(name)
				
				eff = g.get_effect_type(name)
				typ = eff.type
				msg_type = "neutral"
				if typ in ["good", "info"]:
					msg_type = "info"
				elif typ == "bad":
					msg_type = "good"
				
				self.add_msg(eff.remove_msg, msg_type)
				
				if name == "Enlarged" or name == "Reduced":
					self.recalc_max_hp()
					
		for mon in self.visible_monsters():
			name = mon.type.name
			if mon.check_alerted():
				mon.alerted()
				mon.target_entity(self)
		
	def stealth_mod(self):
		stealth = stat_mod(self.DEX)
		if self.has_status("Reduced"):
			stealth += 3
		elif self.has_status("Enlarged"):
			stealth -= 3
			
		return stealth		
				
	def stealth_roll(self):
		return gauss_roll(self.stealth_mod())	