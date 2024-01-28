from enum import Enum
from utils import *
from projectile import SpellProjectile


class SpellCategory(Enum):
	BENEFICIAL = 1
	HARMFUL = -1
	
class SpellAOEType(Enum):
	NONE = 0
	SINGLE = 1
	RADIUS = 2

class Spell:
	g = None
	
	def __init__(self, name, category, spell_range=5,
		att_save=None, power=10, proj_name=None,
		u_resist_msg="", mon_resist_msg="", aoe_type=SpellAOEType.NONE
	):
		 	
		#Category can be one of: Beneficial, Harmful
		
		self.name = name
		self.proj_name = proj_name
		self.category = category
		self.power = power
		self.range = spell_range
		self.u_resist_msg = u_resist_msg
		self.mon_resist_msg = mon_resist_msg
		self.att_save = att_save
		
	def saving_throw(self, target):
		if not self.att_save:
			return False
		match self.att_save:
			case "DEX":
				stat = target.DEX
			case "WIS":
				stat = target.WIS
			case _:
				return False
		
		save_roll = gauss_roll(stat_mod(stat))
		return save_roll >= self.power
		
	def do_spell_effect(self, attacker, pos):
		g = self.g
		ent = g.entity_at(pos)
		if ent:
			self.on_hit(attacker, ent)
			
	def on_hit(self, caster, ent):
		if self.saving_throw(ent):
			mon_msg = self.mon_resist_msg.replace("<monster>", ent.get_name())		
			if mon_msg.startswith(ent.name):
				mon_msg = mon_msg.capitalize()
				
			ent.add_msg_u_or_mons(self.u_resist_msg, mon_msg)
		else:
			self.do_effect(caster, ent)
			
	def cast(self, caster, target):
		g = self.g
		use_projectile = self.att_save == "ranged"
		
		if use_projectile:
			caster.use_energy(100)
			acc = stat_mod(caster.INT)
			proj = SpellProjectile(self, accuracy=acc, name=self.proj_name, max_range=self.range)
			caster.shoot_projectile_at(target.pos, proj)
		else:
			g.display_projectile_animation(caster.pos, target.pos)
			self.do_spell_effect(caster, target.pos)
		
	def do_effect(self, caster, target):
		pass
		
class FlameSpell(Spell):
 	
	def __init__(self):
		super().__init__(
			"Flame",
			proj_name="flame",
			category=SpellCategory.HARMFUL,
			spell_range=7,
			att_save="ranged"
		)
 		
	def do_effect(self, caster, target):
		damage = target.apply_armor(dice(1, 8))
		msg = make_damage_msg(f"The flame hits {target.get_name()}", caster, damage)	
		target.combat_msg(msg)
		target.take_damage(damage, caster)
		
class ConfusionSpell(Spell):
 	
	def __init__(self):
		super().__init__(
			"Confusion",
			category=SpellCategory.HARMFUL,
			spell_range=16,
			att_save="WIS",
			power=12,
			u_resist_msg="You resist the effect.",
			mon_resist_msg="<monster> resists the effect."
		)
 		
	def do_effect(self, caster, target):
		target.add_status("Confused", rng(10, 30))
		