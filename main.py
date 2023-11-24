import random, math
import curses
from board import *
from utils import *

from game_inst import Game

g = Game()


def main():
	g.init_game()
	player = g.get_player()
	
	while True:
		curses.flushinp()
		char = g.get_char()
		valid = g.process_key_input(char)
		if valid:	
			g.do_turn()
		g.draw_board()
		
try:
	main()
except:
	g.deinit_window()				
	raise
finally:
	g.deinit_window()