from utils import *

class Projectile:
	
	def __init__(self, accuracy=0, can_crit=False, name="projectile"):
		self.accuracy = accuracy
		self.name = name
		self.dmg = Dice(1, 4)
		self.dmg_mod = 0
		self.short_range = 999
		self.long_range = 999
		self.final_pos = None
		self.can_crit = can_crit
		
	def roll_damage(self, crit=False):
		dmg = self.dmg.roll()
		if crit:
			dmg += self.dmg.roll()
			
		return max(dmg + self.dmg_mod, 1)
		
	def to_hit_prob(self, attacker, defender):
		dist = attacker.pos.square_dist(defender.pos)
		if dist > self.long_range:
			return 0.0
			
		penalty = calc_ranged_penalty(dist, self.short_range, self.long_range)
		ev = defender.ranged_evasion()
		
		prob = gauss_roll_prob(self.accuracy - penalty, ev)
		return prob
		
	def damage_msg(self, attacker, defender, damage):
		return make_damage_msg(f"The {self.name} hits {defender.get_name()}", attacker, damage)	
	
	def on_hit(self, attacker, defender, margin):
		crit = False
		
		if attacker.is_player() and self.can_crit and margin >= 5:
			crit = one_in(9)
		
		damage = self.roll_damage(crit)
		damage = defender.apply_armor(damage)
		msg = self.damage_msg(attacker, defender, margin)
		defender.combat_msg(msg) 
		if damage > 0 and crit:
			attacker.add_msg("Critical hit!", "good")
		
		defender.take_damage(damage, attacker)
		if defender.is_alive() and defender.is_monster(): 
			if attacker.is_player():
				defender.alerted()
			
class SpellProjectile(Projectile):
	
	def __init__(self, spell, accuracy=0, name="spell effect", max_range=5):
		super().__init__(accuracy=accuracy, name=name)
		self.short_range = max_range
		self.long_range = max_range
		self.spell = spell
		
	def on_hit(self, attacker, defender, margin):
		self.spell.do_spell_effect(attacker, defender.pos)
		if defender.is_alive() and defender.is_monster(): 
			if attacker.is_player():
				defender.alerted()