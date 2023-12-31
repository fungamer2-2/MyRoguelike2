class Projectile:
	
	def __init__(self, accuracy=0, name="projectile"):
		self.accuracy = accuracy
		self.name = name
		self.dmg_dice = 1
		self.dmg_sides = 4
		