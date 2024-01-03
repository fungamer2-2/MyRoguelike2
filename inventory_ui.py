import curses
from items import *
from text_menu import GameTextMenu

def item_display_name(player, item):
	name = item.name
	
	if item is player.armor:
		name += " (worn)"
	return name

def display_item(g, item):
	player = g.get_player()
	screen = g.screen
	screen.erase()
	
	menu = GameTextMenu(g)
	
	menu.add_text(item_display_name(player, item))
	menu.add_text(item.description)
	menu.add_line()
	if isinstance(item, Armor):
		menu.add_text(f"Protection: {item.protection}")
		menu.add_text(f"Encumbrance: {item.encumbrance}")
		if item.stealth_pen > 0:
			menu.add_text(f"Stealth penalty: {-item.stealth_pen}")
		menu.add_line()
	elif isinstance(item, Weapon):
		menu.add_text(f"Base damage: {item.damage}")
		if item.finesse:
			menu.add_text("This is a finesse weapon.")
		if item.heavy:
			menu.add_text("This weapon is heavy; attacking with it takes a bit longer.")
			
		
	use_text = "Use"
	if isinstance(item, Weapon):
		use_text = "Wield"
	elif isinstance(item, Armor):
		use_text = "Wear"
	
	menu.add_text(f"U - {use_text}")
	menu.add_text("D - Drop")
	menu.add_text("Enter - cancel")
	menu.display()
	
	while True:
		code = menu.getch()
		
		if code == 10:
			return False
		elif chr(code) == "u":
			player.use_item(item)
			return True
		elif chr(code) == "d":
			player.drop_item(item)
			return True
			
def consolidate_inventory_display(player):
	counts = {}
	items = {}
	for item in player.inventory:
		name = item_display_name(player, item)
		if name not in counts:
			counts[name] = 0
			items[name] = item
		counts[name] += 1
	
	display = []
	for name in sorted(items.keys()):
		num = counts[name]
		item = items[name]
		if num > 1:
			name += f" (x{num})"
		display.append((name, item))
		
	return display

def inventory_menu(g):
	player = g.get_player()
	
	display = consolidate_inventory_display(player)
			
	screen = g.screen
	scroll = 0
	num_items = len(display)
	max_scroll = max(0, num_items - 9)
		
	can_scroll = max_scroll > 0
		
	display_title = "View which item? Enter a number from 1 - 9, then press Enter (0 to cancel)."
	if can_scroll:
		display_title += " (W and S keys to scroll)"
		
	select = 0
	
	
	while True:
		screen.erase()
		screen.addstr(0, 0, display_title)
		num_displayed = min(num_items, 9)
		for i in range(num_displayed):
			index = i + scroll
				
			name, item = display[index]
			color = curses.A_REVERSE if i == select else 0
			screen.addstr(i + 2, 0, str(i+1), color)
			
			string = f" - {name}"
			if i == 0 and scroll > 0:		
				string += "    [↑]"
			elif i == num_displayed - 1 and scroll < max_scroll:
				string += "    [↓]"
				
			screen.addstr(i + 2, 2, string)
		screen.refresh()
		key = screen.getch()
		char = chr(key)
			
		if can_scroll:
			if char == "w":
				scroll -= 1
			elif char == "s":
				scroll += 1
			scroll = clamp(scroll, 0, max_scroll)
			
		_, item = display[scroll + select]
			
		if char == "0":
			return False
		
		elif char in "123456789":
			value = int(char) - 1
			if value < len(display):
				select = value
			
		if key == 10 and display_item(g, item):
			return True
		screen.erase()