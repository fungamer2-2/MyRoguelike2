from collections import deque

class Message:
	
	def __init__(self, msg):
		self.text = msg
		self.count = 1

class MessageLog:
	
	def __init__(self, capacity):
		self.msgs = deque(maxlen=capacity)
		
	def add_message(self, msg):
		if self.msgs and self.msgs[-1].text == msg: #Combine similar messages
			self.msgs[-1].count += 1
		else:
			self.msgs.append(Message(msg))
			
	def get_messages(self, num):
		messages = []
		for msg in reversed(self.msgs):
			text = msg.text
			if msg.count > 1:
				text += f" (x{msg.count})"
			messages.append(text)
			num -= 1
			if num <= 0:
				break
		messages.reverse()
		return messages