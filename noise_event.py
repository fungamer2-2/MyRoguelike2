
class NoiseEvent:
	
	def __init__(self, pos, vol, src=None):
		self.pos = pos
		self.src = None
		self.loudness = vol