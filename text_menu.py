import os, textwrap

class GameTextMenu:
	
	def __init__(self, g):
		self.screen = g.screen
		self.g = g
		size = os.get_terminal_size()
		self.termwidth = size.columns
		self.msg = []
		
	def add_text(self, txt):
		txt = str(txt)
		self.msg.extend(textwrap.wrap(txt, self.termwidth))
		
	def add_line(self):
		self.msg.append("")
		
	def clear_msg(self):
		self.msg.clear()
	
	def display(self):
		self.screen.clear()
		for i in range(len(self.msg)):
			self.screen.addstr(i, 0, self.msg[i])
		self.screen.refresh()
			
	def close(self):
		self.g.draw_board()
		
	def getch(self):
		return self.screen.getch()
		
	def getchar(self):
		return chr(self.getch())
		
	def wait_for_enter(self):
		while self.getch() != 10: pass