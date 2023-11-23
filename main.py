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
		valid = False
		if char == "w":
			valid = True
			player.move_dir(0, -1)
		elif char == "s":
			valid = True
			player.move_dir(0, 1)
		elif char == "a":
			valid = True
			player.move_dir(-1, 0)
		elif char == "d":
			valid = True
			player.move_dir(1, 0)
		elif char == " ":
			valid = True
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