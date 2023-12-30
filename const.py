WALL_SYMBOL = "#"
PLAYER_SYMBOL = "@"
STAIR_SYMBOL = ">"

MESSAGE_LOG_CAPACITY = 100

MIN_HIT_MISS_PROB = 4

SHIELD_BONUS = 3

COLOR_SILVER = 7
COLOR_GRAY = 8
COLOR_RED = 9
COLOR_GREEN = 10
COLOR_YELLOW = 11
COLOR_BLUE = 12
COLOR_CYAN = 14
COLOR_BLUE1 = 21
COLOR_DODGER_BLUE2 = 27
COLOR_DEEP_PINK2 = 167

SAVED_GAME_PATH = "gamedata.pkl"

MSG_TYPES = {
	"neutral": 0,
	"good": COLOR_GREEN,
	"bad": COLOR_RED,
	"warning": COLOR_YELLOW,
	"info": COLOR_BLUE,
	"input": COLOR_CYAN
}

from enum import Enum

class ItemUseResult:
	NOT_USED = 0 #Item was not used
	USED = 1 #Item was used, but should not be consumed
	CONSUMED = 2 #Item was used, and should be consumed

ANIMATION_DELAY = 0.04