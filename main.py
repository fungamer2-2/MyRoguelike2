import random, math
import curses
from board import *
from utils import *
from game_inst import Game

g = Game()
g.init_game()

player = g.get_player()

while True:
	curses.flushinp()
	char = g.get_char()
	if char == "w":
		player.move_dir(0, -1)
	elif char == "s":
		player.move_dir(0, 1)
	elif char == "a":
		player.move_dir(-1, 0)
	elif char == "d":
		player.move_dir(1, 0)
		
	g.do_turn()
	g.draw_board()				
