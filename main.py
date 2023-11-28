from game_inst import Game

g = Game()

def main():
	g.init_game()
	while True:
		char = g.get_char()
		if g.process_key_input(char):	
			g.do_turn()
		g.draw_board()
		
try:
	main()
except:
	g.deinit_window()				
	raise
finally:
	g.deinit_window()