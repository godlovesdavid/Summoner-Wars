from tkinter import Tk as Window, BooleanVar, StringVar

# **********************************CONSTANTS***************************************
DEFAULT_MOVERS = 3  # movers allowed per turn
DEFAULT_ATTACKERS = 3
DEFAULT_MOVES = 2  # number of moves per unit per turn
DEFAULT_ATTACKS = 1
DEFAULT_DRAWS = 5
DEFAULT_HIT_VALUE = 3

# **********************************GLOBAL VARIABLES***************************************
factions = []
summoners = []
teams = [[], []]  # allow 2 teams
board = []
modifiers = []  # list of Mods on cards and objects
gamemods = [] #mods that get used like autousing abilities

# selection variable is like a StringVar or a BooleanVar but sets value to selection.
class SelectionVar(BooleanVar):
	def __init__(self, master=None, name=None):
		super().__init__(master=master, value=False, name=name)
		self.selection = None

	def set(self, value):
		self.selection = value
		BooleanVar.set(self, True)


window = Window()
window.resizable(width=False, height=False)
messagevar = StringVar(window)  # info text for player
selectvar = SelectionVar(window)  # vars to save choices from user (e.g. cards)
