from collections import defaultdict

class EventBus:
	
	def __init__(self):
		self.events = defaultdict(list)
		
	def get_subscribers(self, event):
		return self.events[event]
		
	def add_subscriber(self, event, func):
		self.get_subscribers(event).append(func)
	
	def notify(self, event, **params):
		for func in self.get_subscribers(event):
			func(**params)

	