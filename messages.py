from collections import deque
from const import *

class Message:
	
	def __init__(self, msg, type):
		self.type = type
		self.text = msg
		self.count = 1
		
class MessageLog:
	
	def __init__(self, capacity):
		self.msgs = deque(maxlen=capacity)
		
	def add_message(self, msg, typ="neutral"):
		if not msg:
			return
		if typ not in MSG_TYPES:
			raise ValueError(f"invalid message type {typ!r}")
		
		msg = str(msg)
		combine = False
		if self.msgs:
			last = self.msgs[-1]
			combine = last.type == typ and last.text == msg
			
		if combine: #Combine similar messages
			self.msgs[-1].count += 1
		else:
			self.msgs.append(Message(msg, typ))
			
	def get_messages(self, num):
		messages = []
		for msg in reversed(self.msgs):
			text = msg.text
			if msg.count > 1:
				text += f" (x{msg.count})"
			messages.append((text, msg.type))
			num -= 1
			if num <= 0:
				break
		messages.reverse()
		return messages