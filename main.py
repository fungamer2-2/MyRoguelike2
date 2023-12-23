from game_inst import Game
import atexit

g = Game()
atexit.register(g.save)

def main():
	g.init_game()
	player = g.get_player()
	
	while player.is_alive():
		if g.process_input():
			g.do_turn()		
	g.game_over()
		
try:
	main()
except:
	g.deinit_window()	
	raise
finally:
	g.deinit_window()