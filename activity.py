from abc import ABC, abstractmethod

class Activity:
	
	def __init__(self, name, duration):
		self.name = name
		self.duration = duration
	
	@abstractmethod	
	def on_finished(self, player):
		pass
		
class EquipArmorActivity(Activity):
	
	def __init__(self, armor, duration):
		super().__init__(f"putting on your {armor.name}", duration)
		self.armor = armor
		
	def on_finished(self, player):
		player.equip_armor(self.armor)
		
class RemoveArmorActivity(Activity):
	
	def __init__(self, armor, duration, drop=False):
		super().__init__(f"taking off your {armor.name}", duration)
		self.drop = drop
		
	def on_finished(self, player):
		armor = player.armor
		player.unequip_armor()
		if self.drop:
			player.quick_drop(armor)