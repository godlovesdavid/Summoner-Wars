from _pickle import Pickler, Unpickler
from os.path import lexists
from random import randint, shuffle

from PIL.Image import FLIP_LEFT_RIGHT
from PIL.ImageTk import PhotoImage, Image

from summonerwars.data import *


# variables.
view = None
cardcaches = {}
justloaded = False
PHASES = []
boardwidth = 6
boardheight = 8
gamemods = [] #game mods get used every update like passive abilities, except they also can expire

whoseturn = None
phase = None
subphase = 0
action = None
subaction = 0

# give name of a thing (usually its class name).
def name(thing):
	str = ''
	for char in thing.__class__.__name__:
		if char.isupper():
			str += ' '
		str += char
	return str.lstrip()


def setwhoseturn(summoner):
	global whoseturn
	whoseturn = summoner


def setrepaintable(repaintable):
	global view
	view = repaintable


def cachepics():
	for summoner in summoners:
		for card in summoner.deck:
			cardcaches[card] = {}
			cardcaches[card]['cardphoto'] = PhotoImage(Image.open(card.cardpicpath).resize((368, 240), Image.ANTIALIAS))
			if 'picpath' in card.__dict__:
				pic = Image.open(card.picpath)
				if summoner.playernum is 1 or summoner.playernum is 2:  #flip it if on right side of board
					pic = pic.transpose(FLIP_LEFT_RIGHT)
				cardcaches[card]['photo'] = PhotoImage(pic)
			else:  #use the card pic as board pic if no board pic given
				cardcaches[card]['photo'] = PhotoImage(Image.open(card.cardpicpath).resize((100, 67), Image.ANTIALIAS))
		summoner.faction.logophoto = PhotoImage(Image.open(summoner.faction.path + r'\symbol-lrg.png').resize((15, 15)))


def saveturn():
	filename = 'lastturn'
	if lexists(filename):
		file = open(filename, 'wb')
	else:
		file = open(filename, 'xb')

	saver = Pickler(file)
	saver.dump(summoners)
	saver.dump(teams)
	saver.dump(board)
	saver.dump(boardwidth)
	saver.dump(boardheight)
	saver.dump(modifiers)
	saver.dump(gamemods)
	saver.dump(whoseturn)
	saver.dump(phase)
	saver.dump(subphase)
	#cannot save action, because will give error with inner methods (like render).
	file.close()


def loadlastturn():
	global justloaded, boardwidth, boardheight, gamemods, whoseturn, phase, subphase, action, subaction
	file = open('lastturn', 'rb')
	loader = Unpickler(file)
	clear(summoners)
	clear(teams)
	clear(board)
	clear(modifiers)
	clear(gamemods)

	extend(summoners, loader.load())
	extend(teams, loader.load())
	extend(board, loader.load())
	boardwidth = loader.load()
	boardheight = loader.load()
	extend(modifiers, loader.load())
	extend(gamemods, loader.load())
	cachepics()
	whoseturn = loader.load()
	phase = loader.load()
	subphase = loader.load()
	file.close()

	justloaded = True
	phase()


# make every obj in a given list that is on the board selectable and wait for user to select one and return it.
def choosefrom(lst, msg=''):
	messagevar.set(msg)

	# draw selectable areas.
	view.repaint(lst, whoseturn=whoseturn, phase=phase, subphase=subphase)

	# wait for choice from user.
	window.wait_variable(selectvar)
	return selectvar.selection


# -----------------------------------Base functions---------------------------------------
# Base functions deal with lists in a game-compatible manner. TODO: make these undoable

# get top of card stack without removing it.
def top(stack):
	if len(stack) > 0:
		return stack[len(stack) - 1]
	return None


# clear a list.
def clear(lst):
	# del lst[0:len(lst)]
	lst.clear()


# exactly same as list.remove(), but removes all instances instead of one.
def remove(object, lst):
	for thing in lst.copy():
		if thing is object:
			lst.remove(thing)


# append() but allow no duplicates.
def add(object, lst, index=None):
	for element in lst:
		if element is object:
			return

	if index is None:
		lst.append(object)
	else:
		lst.insert(index, object)


# move card to another stack.
def move(card, stack, index=None):
	if card.pos is not None:
		card.pos.remove(card)
	if index is None:
		stack.append(card)
	else:
		stack.insert(index, card)
	card.pos = stack


# move card under another card (or to the bottom of a stack).
def moveunder(card, thing):
	card.pos.remove(card)
	if isinstance(thing, list):
		thing.insert(0, card)
		card.pos = thing
	else:
		thing.pos.insert(thing.pos.index(thing), card)
		card.pos = thing.pos


# exchange positions of two cards.
def switchplaces(card1, card2):
	pos = card1.pos
	move(card1, card2.pos)
	move(card2, pos)


# remove duplicate elements from list.
def removeduplicates(lst):
	index = 0
	while index < len(lst):
		compareindex = index + 1
		while compareindex < len(lst):
			if lst[index] is lst[compareindex]:
				del lst[compareindex]
				compareindex -= 1
			compareindex += 1

		index += 1


def isempty(lst):
	return len(lst) is 0


def extend(lst, lst2):
	lst.extend(lst2)


def execute(actionobj):
	update(action=actionobj, subaction=1)
	actionobj.render()

	update(action=actionobj, subaction=2)
	result = actionobj.apply()

	update(action=actionobj, subaction=3)
	return result


# -----------------------------------Special classes---------------------------------------

#Actions are objects that hold information of game occasions as opportunities for game modification.
class Action(object):
	def render(self):
		pass

	def apply(self):
		pass


class Summon(Action):
	def __init__(self, summoner, unit, pos, free=False):
		self.agent = summoner
		self.target = unit
		self.pos = pos
		self.free = free

	def render(self):
		pass

	def apply(self):
		if not self.free:
			for magic in range(self.target.cost):
				move(top(self.agent.magicpile), self.agent.discardpile)
		move(self.target, self.pos)


#invoke the use method of an event card.
class PlayEvent(Action):
	def __init__(self, player, event):
		self.agent = player
		self.target = event

		#save current occasion details.
		self.whoseturn = whoseturn
		self.phase = phase
		self.subphase = subphase
		self.action = action
		self.subaction = subaction

	def render(self):
		pass

	def apply(self):
		if self.target.use(self.whoseturn, self.phase, self.subphase, self.action, self.subaction) is False:
			return False
		if self.target.discardonuse:
			self.agent.discard(self.target)
		print('Played ' + name(self.target))


#return list of cells that a card can be summoned onto.
class GetSummonCells(Action):
	def __init__(self, unit):
		self.agent = unit

	def render(self):
		self.lst = []
		for wall in self.agent.owner.deck.walls:
			if onboard(wall):
				self.lst += cellsfrom(wall, spaces=1, onlyempties=True)

	def apply(self):
		return self.lst


# scan battlefield for possible targets from unit. A unit cannot attack something if line of sight is blocked. If spaces param is not set, it will default to the attacker's range.
class GetTargetCards(Action):
	def __init__(self, attacker, range):
		self.agent = attacker
		self.range = range

	def render(self):
		self.lst = straightlinecardsfrom(self.agent, spaces=self.range, blockedlos=True)

	def apply(self):
		return self.lst


#get cells that a unit can move to.
class GetMoveCells(Action):
	def __init__(self, mover):
		self.agent = mover

	def render(self):
		self.lst = cellsfrom(self.agent, spaces=self.agent.movesleft, onlyempties=True)

	def apply(self):
		return self.lst


#wound action decreases the current life of a card.
class Wound(Action):
	def __init__(self, attacker, target, numwounds=1):
		self.agent = attacker
		self.target = target
		self.count = numwounds

	def render(self):
		pass

	def apply(self):
		# apply attacks.
		self.target.life -= self.count
		print('Wounded', name(self.target), 'by', self.count)

		# clean up corpse if killed it.
		if self.target.life <= 0:
			print('Killed', name(self.target))
			# put in magic pile.
			move(self.target, self.agent.owner.magicpile)

		return self.count


#heal action increases the current life of a card.
class Heal(Action):
	def __init__(self, healer, target, numheals):
		self.agent = healer
		self.target = target
		self.count = numheals

	def render(self):
		pass

	def apply(self):
		print('Healed', name(self.target), 'by', str(self.target.maxlife - self.target.life), '.')
		self.target.life += self.count
		if self.target.life > self.target.maxlife:
			self.target.life = self.target.maxlife

		return self.count


# attack object that renders and applies itself.
#there are 5 updates during this whole attack.
# 1. before rendering attack 2. after rendering attack 3. trying to wound target based on render 4. (optional) destroyed target 5. finished attack
class Attack(Action):
	def __init__(self, attacker, target):
		self.agent = attacker
		self.target = target

		self.rolltohit = DEFAULT_HIT_VALUE  #roll value for a hit
		self.startcell = target.pos  #remember target position before it gets killed and sent somewhere else

	#let abilities change target or attacker before rendering attack.
	def render(self):
		#roll.
		self.rolllist = execute(Roll(self, self.agent.atk))

		#calculate number of hits.
		self.numhits = len([roll for roll in self.rolllist if roll >= self.rolltohit])

	#wound target and save number of wounds.
	def apply(self):
		self.numwounds = execute(Wound(self.agent, self.target, self.numhits))

		#decrement attacks left.
		self.agent.attacksleft -= 1
		add(self.agent, self.agent.owner.attacked)

		return self.numwounds


#move action moves a unit somewhere and adds it to list of already moved units.
class Move(Action):
	def __init__(self, mover, destcell):
		self.agent = mover
		self.target = destcell
		self.startcell = mover.pos

	def render(self):
		# calculate distance.
		self.count = abs(self.target.x - self.agent.pos.x) + abs(self.target.y - self.agent.pos.y)

	def apply(self):
		# go there.
		move(self.agent, self.target)
		self.agent.movesleft -= self.count
		add(self.agent, self.agent.owner.moved)

		return self.count


#roll action returns a list of integers ranging 1-6 each.
class Roll(Action):
	def __init__(self, roller, numdice):
		self.agent = roller
		self.count = numdice

	def render(self):
		self.lst = [randint(1, 6) for roll in range(self.count)]
		for roll in self.lst:
			print('Rolled', roll)

	def apply(self):
		return self.lst


#card stack, which is just a list but different contains checking.
class Stack(list):
	def __init__(self, iterable=()):
		super(Stack, self).__init__(iterable)

	#contains method different from normal in that it checks matching type and value (instead of just value).
	def __contains__(self, item):
		for element in self:
			if element is item:
				return item


# board cell, a card stack, but with coordinates.
class Cell(Stack):
	def __init__(self, x, y):
		super(Cell, self).__init__(self)
		self.x = x
		self.y = y

	#two cells are == if they have the same coordinates.
	def __eq__(self, other):
		return isinstance(other, Cell) and self.x is other.x and self.y is other.y

	#string method gives readable nonzero based coordinates.
	def __str__(self):
		return '(' + str(self.y + 1) + ', ' + str(boardwidth - self.x) + ')'


class GameMod(object):
	def __init__(self, owner, turns=99999):
		self.owner = owner
		self.turns = turns
		add(self, gamemods)

	def use(self, whoseturn, phase, subphase, action, subaction):  #gets called every game update
		pass


# temporary modifier of a thing's attribute.
class Mod(object):
	def __init__(self, thing, attname, value, turns=0):  #last until next update by default
		self.thing = thing
		self.attname = attname
		self.turns = turns

		self.oldval = thing.__dict__[attname]

		#set the attribute's value.
		thing.__dict__[attname] = value

		#add this mod to global list of modifiers.
		add(self, modifiers)

	# undo the modification on delete.
	def undo(self):
		#set attribute value to old value.
		self.thing.__dict__[self.attname] = self.oldval


#offset modifier of a thing's attribute.
class OffsetMod(object):
	def __init__(self, thing, attname, offset, turns=0):
		self.thing = thing
		self.attname = attname
		self.turns = turns
		self.offset = offset

		#offset the attribute's value.
		thing.__dict__[attname] += offset

		#add this mod to global list of modifiers.
		add(self, modifiers)

	def undo(self):
		#undo the offset.
		self.thing.__dict__[self.attname] -= self.offset


#addition to list modifier.
class ListAddMod(object):
	def __init__(self, lst, element, turns=0):
		self.lst = lst
		self.turns = turns
		self.element = element

		#add to list.
		add(element, lst)

		#add this mod to global list of modifiers.
		add(self, modifiers)

	def undo(self):
		#remove from list.
		remove(self.element, self.lst)


class ListRemMod(object):
	def __init__(self, lst, element, turns=0):
		self.lst = lst
		self.turns = turns
		self.element = element

		#add to list.
		remove(element, lst)

		#add this mod to global list of modifiers.
		add(self, modifiers)

	def undo(self):
		#remove from list.
		add(self.element, self.lst)


# Unit ability.
class Ability(object):
	# set passive things here.
	def __init__(self, wielder, desc, cost=0):
		self.wielder = wielder
		self.cost = cost
		self.bought = False
		self.used = False #as in pressed use button
		self.passiveused = False
		self.useenabled = True
		self.passiveuseenabled = True
		self.canbuy = False  #to be updated constantly at update()
		self.canuse = False
		self.desc = desc

		# add self to wielder's abilities.
		add(self, wielder.abilities)

	''' set conditions for availability of purchase (not used if costless).

	Pass these variables:
	whoseturn - whose turn it is as a Summoner object
	phase - of the game, like "MOVE BEGIN"
	occasion - specific occasion of the game, like 'destroyed'
	action - action object given by occasion, which correspond to occasion as in the following:
	'changed' : indicating a change in game has occurred
	'initialized GetTargetCards'
	'rendered GetMoveCells'
	'''

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return False

	# set conditions for availability of activation.
	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return False

	def use(self, whoseturn, phase, subphase, action, subaction):
		pass

	def passiveuse(self, whoseturn, phase, subphase, action, subaction): #auto run every update
		pass

	# reset ability (usually every turn) so that it can be used again.
	def refresh(self):
		self.bought = False
		self.used = False
		self.passiveused = False


# -----------------------------------Test functions---------------------------------------

# test functions give a list based on what is asked.
def summonablecards(summoner, type=None, ability=None, free=False):
	lst = []
	for card in summoner.hand:
		if isinstance(card, Unit): #must be at least a unit
			if (not type or isinstance(card, type)) and (free or card.cost <= len(summoner.magicpile)):
				if not ability:
					add(card, lst)
				else:
					for a in card.abilities:
						if isinstance(a, ability):
							add(card, lst)
	return lst


def playableevents(summoner):
	return [card for card in summoner.hand if isinstance(card, Event) and card.isuseenabled(whoseturn, phase, subphase, action, subaction) and len(summoner.magicpile) >= card.cost]


def ismoveable(cell):
	return len(cell) is 0


def moveables(summoner):
	return [card for card in cardsonboard(type=Unit, owners=[summoner]) if canmove(card)]


def canmove(unit):
	return onboard(unit) and unit.life > 0 and unit.movesleft > 0 and (len(unit.owner.moved) < unit.owner.allowedmovers or unit in unit.owner.moved)


# see what unit, belonging to summoner, is on board and can attack.
def attackers(summoner):
	return [unit for unit in cardsonboard(type=Unit, owners=[summoner]) if canattack(unit)]


def canattack(unit):
	return onboard(unit) and unit.life > 0 and unit.atk > 0 and unit.attacksleft > 0 and (len(unit.owner.attacked) < unit.owner.allowedattackers or unit in unit.owner.attacked)


def wallcells(summoner):
	lst = []
	for wall in summoner.deck.walls:
		lst += cellsfrom(wall, spaces=1, onlyempties=True)
	return lst


# gives card on board given type and/or owner.
def cardsonboard(owners=None, type=None, faction=None, onlyattackables=True, ability=None):
	lst = []
	for x in range(boardwidth):
		for y in range(boardheight):
			for card in board[x][y]:
				if (not owners or card.owner in owners) and (not type or isinstance(card, type)) and (not faction or faction is card.faction) and (not onlyattackables or 'life' in card.__dict__ and card.life > 0):
					#check if has ability.
					if not ability:
						add(card, lst)
					else:
						if isinstance(card, Unit):
							for a in card.abilities:
								if isinstance(a, ability):
									add(card, lst)
									break
	return lst


# return list of cells.
def cellsonboard(team=None, onlyempties=False):
	ymin = 0
	ymax = boardheight

	if team is not None:
		# get team num first.
		teamnum = teams.index(team)
		if teamnum is 0:
			ymin = 0
			ymax = int(boardheight / 2)
		elif teamnum is 1:
			ymin = int(boardheight / 2)
			ymax = boardheight

	lst = []
	for x in range(boardwidth):
		for y in range(ymin, ymax):
			if not onlyempties or len(board[x][y]) is 0:
				add(board[x][y], lst)
	return lst


# return a list of cells that a thing (card or cell) is adjacent to.
def cellsfrom(thing, spaces, onlyempties=False, onlyreachables=True, includeowncell=False, directions='nswe'):
	if not onboard(thing):
		return []

	lst = []

	# get position.
	if isinstance(thing, Card):  # for card
		x = thing.pos.x
		y = thing.pos.y
	else:  # for cell
		x = thing.x
		y = thing.y

	if includeowncell:
		add(board[x][y], lst)

	if spaces is 0:
		return lst

	# for ea. neighboring cell in directions
	for dir in directions:
		cell = None
		if dir is 'n' and y + 1 < boardheight:
			cell = board[x][y + 1]
			searchdirs = 'new'
		elif dir is 'e' and x + 1 < boardwidth:
			cell = board[x + 1][y]
			searchdirs = 'ens'
		elif dir is 'w' and x - 1 >= 0:
			cell = board[x - 1][y]
			searchdirs = 'nws'
		elif dir is 's' and y - 1 >= 0:
			cell = board[x][y - 1]
			searchdirs = 'ews'
		elif cell is None:
			continue

		# test if cell passes the filter test.
		if not onlyempties or isempty(cell):
			# add to list if so.
			add(cell, lst)
			# from here, also search given directions.
			lst += cellsfrom(cell, spaces=spaces - 1, onlyempties=onlyempties, onlyreachables=onlyreachables, includeowncell=False, directions=searchdirs)

		#but also search more if blocked out cells are included.
		elif not onlyreachables:
			lst += cellsfrom(cell, spaces=spaces - 1, onlyempties=onlyempties, onlyreachables=onlyreachables, includeowncell=False, directions=searchdirs)

	removeduplicates(lst)
	return lst


# give list of cards from card or cell.
def cardsfrom(thing, spaces, abilities=None, owners=None, type=None, onlyattackables=True, includeowncell=True, faction=None):
	lst = []
	for cell in cellsfrom(thing, spaces=spaces, includeowncell=includeowncell, onlyreachables=False, onlyempties=False):
		for card in cell:
			if (not owners or card.owner in owners) and (not type or isinstance(card, type)) and (not onlyattackables or 'life' in card.__dict__ and card.life > 0) and (not abilities or not isempty([ability for ability in abilities if ability in card.abilities])) and (not faction or card.faction is faction) and (thing is not card):
				add(card, lst)
	return lst


def straightlinecellsfrom(thing, spaces, onlyempties=False, onlyreachables=True, includeowncell=False, directions='nwse'):
	if not onboard(thing):
		return []

	lst = []

	# get position.
	if isinstance(thing, Card):  # for card
		x = thing.pos.x
		y = thing.pos.y
	else:  # for cell
		x = thing.x
		y = thing.y

	if includeowncell:
		add(board[x][y], lst)

	if spaces is 0:
		return lst

	# for ea. neighboring cell in directions
	for dir in directions:
		cell = None
		if dir is 'n' and y + 1 < boardheight:
			cell = board[x][y + 1]
		elif dir is 'e' and x + 1 < boardwidth:
			cell = board[x + 1][y]
		elif dir is 'w' and x - 1 >= 0:
			cell = board[x - 1][y]
		elif dir is 's' and y - 1 >= 0:
			cell = board[x][y - 1]
		elif cell is None:
			continue

		if not onlyempties or isempty(cell):
			add(cell, lst)

			# from here, also search given directions.
			lst += straightlinecellsfrom(cell, spaces=spaces - 1, onlyempties=onlyempties, onlyreachables=onlyreachables, includeowncell=False, directions=dir)

		elif not onlyreachables:
			lst += straightlinecellsfrom(cell, spaces=spaces - 1, onlyempties=onlyempties, onlyreachables=False, includeowncell=False, directions=dir)

	removeduplicates(lst)
	return lst


def straightlinecardsfrom(thing, spaces, onlyattackables=True, blockedlos=False, directions='nwse'): #blockedlos is blocked line of sight
	lst = []
	for dir in directions:
		for cell in straightlinecellsfrom(thing, spaces=spaces, onlyempties=False, onlyreachables=False, includeowncell=True, directions=dir):
			blocked = False
			for card in cell:
				if (not onlyattackables or 'life' in card.__dict__ and card.life > 0) and (thing is not card):
					add(card, lst)
					# if (thing is not cell) or (isinstance(thing, Card) and thing.pos is not cell): #things on own cell don't block los
					blocked = True
			if blocked and blockedlos:
				break
	return lst


def diagonalcellsfrom(thing, spaces, onlyempties=False, onlyreachables=True, includeowncell=False, directions='1379'):  #numpad directions
	if not onboard(thing):
		return []

	lst = []

	# get position.
	if isinstance(thing, Card):  # for card
		x = thing.pos.x
		y = thing.pos.y
	else:  # for cell
		x = thing.x
		y = thing.y

	if includeowncell:
		add(board[x][y], lst)

	if spaces is 0:
		return lst

	# for ea. neighboring cell in directions
	for dir in directions:
		cell = None
		if dir is '7' and x - 1 >= 0 and y - 1 >= 0:
			cell = board[x - 1][y - 1]
		elif dir is '9' and x + 1 < boardwidth and y - 1 >= 0:
			cell = board[x + 1][y - 1]
		elif dir is '1' and x - 1 >= 0 and y + 1 < boardheight:
			cell = board[x - 1][y + 1]
		elif dir is '3' and x + 1 < boardwidth and y + 1 < boardheight:
			cell = board[x + 1][y + 1]

		elif cell is None:
			continue

		if not onlyempties or isempty(cell):
			add(cell, lst)

			# from here, also search given directions.
			lst += diagonalcellsfrom(cell, spaces=spaces - 1, onlyempties=onlyempties, onlyreachables=onlyreachables, includeowncell=False, directions=dir)

		elif not onlyreachables:
			lst += diagonalcellsfrom(cell, spaces=spaces - 1, onlyempties=onlyempties, onlyreachables=False, includeowncell=False, directions=dir)

	removeduplicates(lst)
	return lst


def diagonalcardsfrom(thing, spaces, onlyattackables=True, blockedlos=False, directions='1379'):  #numpad directions
	lst = []
	for dir in directions:
		for cell in diagonalcellsfrom(thing, spaces=spaces, onlyempties=False, onlyreachables=False, includeowncell=True, directions=dir):
			blocked = False
			for card in cell:
				if (not onlyattackables or 'life' in card.__dict__ and card.life > 0) and (thing is not card):
					add(card, lst)
					blocked = True
			if blocked and blockedlos:
				break
	return lst


# test if two cards are next to each other.
def isadjacent(thing1, thing2):
	if isinstance(thing1, Card):
		return thing1 in cardsfrom(thing2, spaces=1)
	elif isinstance(thing1, Cell):
		return thing1 in cellsfrom(thing2, spaces=1)


# see if something is on board.
def onboard(thing):
	return isinstance(thing, Cell) or isinstance(thing.pos, Cell)


# pressed buy button of an ability.
def buy(ability):
	for cost in range(ability.cost):
		move(top(ability.wielder.owner.magicpile), ability.wielder.owner.discardpile)
	ability.bought = True
	print('Bought', name(ability))
	update()

	#use it if right time.
	if ability.isuseenabled(whoseturn, phase, subphase, action, subaction):
		use(ability)

# pressed use button of an ability.
def use(ability):
	ability.useenabled = False #to prevent recursion
	if ability.use(whoseturn, phase, subphase, action, subaction) is not False:
		ability.used = True
	ability.useenabled = True

	#print result.
	if ability.used:
		print('Used', name(ability))
	else:
		print(name(ability), 'did not activate.')

	update()


# update game things given game 
def update(whoseturn=None, phase=None, subphase=None, action=None, subaction=None):  #action must not be set to None or else it won't pickle
	if whoseturn is None:
		whoseturn = globals()['whoseturn']
	else:
		globals()['whoseturn'] = whoseturn
	if phase is None:
		phase = globals()['phase']
	else:
		globals()['phase'] = phase
	if subphase is None:
		subphase = globals()['subphase']
	else:
		globals()['subphase'] = subphase
	if action is None:
		action = globals()['action']
	else:
		globals()['action'] = action
	if subaction is None:
		subaction = globals()['subaction']
	else:
		globals()['subaction'] = subaction

	# update modifiers.
	for mod in modifiers.copy():
		if mod.turns <= 0:
			mod.undo()
			remove(mod, modifiers)
	for mod in gamemods.copy():
		if mod.turns <= 0:
			remove(mod, gamemods)
		else:
			mod.use(whoseturn, phase, subphase, action, subaction)

	#play events that use outside of event's owner's event phase.
	for summoner in summoners:
		if (phase is not eventphase and whoseturn is summoner) or whoseturn is not summoner:
			for event in [card for card in summoner.hand if isinstance(card, Event)]:
				if event.isuseenabled(whoseturn, phase, subphase, action, subaction) and len(summoner.magicpile) >= event.cost:
					savedwhoseturn = whoseturn  #change turn temporarily if needed
					setwhoseturn(summoner)
					if choosefrom([True, False], msg='Use ' + name(event) + ', ' + name(event.owner) + '?') is True:
						summoner.playevent(event)
						for cost in range(event.cost):
							summoner.discard(top(summoner.magicpile))
					setwhoseturn(savedwhoseturn)

	#update abilities.
	units = cardsonboard(type=Unit)
	if type(action) is GetSummonCells:
		add(action.agent, units)  #include abilities of units being summoned
	elif type(action) is Wound and subaction is 3 and action.target.life <= 0:
		if isinstance(action.target, Unit):
			add(action.target, units)  #include abilities of units being destroyed
	for unit in units:
		for ability in unit.abilities:
			#use passive parts of abilities.
			if ability.passiveuseenabled and not ability.passiveused:
				ability.passiveuseenabled = False #to prevent recursion
				ability.passiveused = ability.passiveuse(whoseturn, phase, subphase, action, subaction)
				ability.passiveuseenabled = True

			#update buttons.
			ability.canbuy = ability.useenabled and unit.owner is whoseturn and not ability.bought and ability.cost > 0 and len(ability.wielder.owner.magicpile) >= ability.cost and ability.isbuyenabled(whoseturn, phase, subphase, action, subaction)
			ability.canuse = ability.useenabled and unit.owner is whoseturn and not ability.used and (ability.bought or ability.cost <= 0) and ability.isuseenabled(whoseturn, phase, subphase, action, subaction)

	#case when a summoner has been destroyed.
	if type(action) is Wound and subaction is 3 and action.target.life <= 0 and isinstance(action.target, Summoner):
		summoner = action.target
		remove(summoner, summoners)
		remove(summoner, summoner.team)

		#move all his cards offboard.
		for x in range(boardwidth):
			for y in range(boardheight):
				for card in board[x][y].copy():
					if card.owner is summoner:
						move(card, summoner.discardpile)

		# determine if a team has won, then exit.
		if len(summoner.team) is 0:
			del teams[teams.index(summoner.team)]
			if len(teams) is 1:
				print('Winner is team', teams.index(teams[0]))
				exit()
		# if not, transfer magic pile to another teammate.
		else:
			for card in summoner.magicpile:
				card.owner = summoner.team[0]
			summoner.team[0].magicpile += summoner.magicpile

		del summoner.drawpile
		del summoner.discardpile
		del summoner.magicpile
		del summoner.hand
		summoner.team = None

	#repaint the screen.
	view.repaint(whoseturn=whoseturn, phase=phase, subphase=subphase)


# -----------------------------------Game ---------------------------------------
def availableabilities():
	return [ability for unit in cardsonboard(owners=[whoseturn], type=Unit) for ability in unit.abilities if ability.canbuy or ability.canuse]


# make new game from up to 4 decks.
# 1st & 3rd decks are team 0.
# 2nd & 4th decks are team 1.
def startbattle(decks):
	assert len(decks) <= 4
	global boardwidth, boardheight, PHASES, whoseturn, phase

	# make board.
	if len(decks) > 2:
		boardwidth += 6
	for col in range(boardwidth):
		add([], board)
		for row in range(boardheight):
			add(Cell(col, row), board[col])

	#declare phases.
	PHASES = (drawphase, summonphase, eventphase, movephase, attackphase, magicphase, refreshphase)

	# put starting cards on board.
	playernum = 0
	for deck in decks:
		add(deck.summoner, globals()['summoners'])  #remember summoners

		#set teams first.
		if playernum is 0 or playernum is 2:
			team = teams[0]
			enemyteam = teams[1]
		elif playernum is 1 or playernum is 3:
			team = teams[1]
			enemyteam = teams[0]

		deck.summoner.setup(playernum=playernum, deck=deck, team=team, enemyteam=enemyteam)

		playernum += 1

	#cache pics.
	cachepics()

	#announce battle.
	# message = 'NEW BATTLE --'
	# for teamnum in range(len(teams)):
	# 	message += ' team ' + str(teamnum) + ': ['
	# 	for playernum in range(len(teams[teamnum])):
	# 		message += name(teams[teamnum][playernum])
	# 		if playernum > 0:
	# 			message += ', '
	# 	message += ']'
	# print(message)

	# roll to see who goes first.
	best = None
	while best is None:
		rolls = {}
		for teamnum in range(len(teams)):
			rolls[teamnum] = randint(1, 6)
			print(name(teams[teamnum][0]) + ' rolled ' + str(rolls[teamnum]))
		for teamnum, result in rolls.items():
			if best is None or rolls[best] < result:
				best = teamnum
			elif rolls[best] is result:
				best = None
		if best is None:
			print("Tie. Rolling again.")
	whoseturn = teams[best][0]
	print('\n==' + name(whoseturn) + "'s Turn (only 2 movers allowed first turn)==")

	# allow only 2 movers first turn.
	Mod(whoseturn, attname='allowedmovers', value=2, turns=1)

	# start from move phase.
	phase = movephase
	saveturn()
	phase()


# draw phase.
def drawphase():
	global subphase
	update(subphase=1)
	abilities = availableabilities()
	while subphase < 3 or not isempty(abilities):
		if subphase is 3:
			msg = 'Abilities available.'
		else:
			msg = 'Draw cards or play ability.'

		# first allow for ability use.
		choice = choosefrom(abilities, msg=msg)
		if choice is None:
			if subphase is 3:
				break
			update(subphase=3)
		elif isinstance(choice, Ability):
			if choice.canbuy:
				buy(choice)
			elif choice.canuse:
				use(choice)

		abilities = availableabilities()

	# draw til 5 in hand.
	while len(whoseturn.hand) < whoseturn.allowedinhand and not isempty(whoseturn.drawpile):
		move(top(whoseturn.drawpile), whoseturn.hand)

	subphase = 2
	update(subphase=2)

	nextphase()


# summon phase.
def summonphase():
	update(subphase=1)
	summonables = summonablecards(whoseturn)
	abilities = availableabilities()
	while subphase < 3 or not isempty(abilities):
		if subphase is 3:
			msg = 'Abilities available.'
		else:
			msg = 'Choose unit to summon\n(' + str(len(summonables)) + ' available).'

		# choose unit in hand.
		choice = choosefrom(summonables + abilities, msg=msg)
		if choice is None:
			if subphase is 3:
				break
			summonables = []
			update(subphase=3)
		elif isinstance(choice, Ability):
			if choice.canbuy:
				buy(choice)
			elif choice.canuse:
				use(choice)
			summonables = summonablecards(whoseturn)
		else:
			# choose cell to summon on
			cell = choosefrom(choice.getsummoncells(), msg='Choose a cell next to wall.')
			if cell is None:
				continue

			#summon choice.
			whoseturn.summon(choice, cell)
			update(subphase=2)
			summonables = summonablecards(whoseturn)

		abilities = availableabilities()

	nextphase()


# events phase.
def eventphase():
	update(subphase=1)
	events = playableevents(whoseturn)
	abilities = availableabilities()
	while subphase < 3 or not isempty(abilities):
		if subphase is 3:
			msg = 'Abilities available.'
		else:
			msg = 'Choose event to use, including walls.\n(' + str(len(events)) + ' available).'

		# choose event card in hand.
		choice = choosefrom(events + abilities, msg=msg)
		if choice is None:
			if subphase is 3:
				break
			events = []
			update(subphase=3)
		elif isinstance(choice, Ability):
			if choice.canbuy:
				buy(choice)
			elif choice.canuse:
				use(choice)
		else:  # events
			if whoseturn.playevent(choice) is False:
				print(name(choice), 'did not activate.')
			else:
				update(subphase=2)
				for cost in range(choice.cost):
					whoseturn.discard(top(whoseturn.magicpile))
			events = playableevents(whoseturn)

		abilities = availableabilities()

	nextphase()


# move phase.
def movephase():
	update(subphase=1)
	units = moveables(whoseturn)
	abilities = availableabilities()
	while subphase < 3 or not isempty(abilities):
		if subphase is 3:
			msg = 'Abilities available.'
		else:
			msg = 'Choose unit to move \n(' + str(whoseturn.allowedmovers - len(whoseturn.moved)) + ' left).'

		# choose unit to move.
		choice = choosefrom(units + abilities, msg=msg)
		if choice is None:
			if subphase is 3:
				break
			units = []
			update(subphase=3)
		elif isinstance(choice, Ability):
			if choice.canbuy:
				buy(choice)
			elif choice.canuse:
				use(choice)
			units = moveables(whoseturn)
		else:
			# choose cell to move to.
			cell = choosefrom(choice.getmovecells(), msg='Choose cell to move to.')
			if cell is None:
				continue

			#move choice.
			choice.move(cell)
			update(subphase=2)
			units = moveables(whoseturn)

		abilities = availableabilities()

	nextphase()


# attack phase.
def attackphase():
	update(subphase=1)
	units = attackers(whoseturn)
	abilities = availableabilities()
	while subphase < 3 or not isempty(abilities):
		if subphase is 3:
			msg = 'Abilities available.'
		else:
			msg = 'Choose attacker\n(' + str(whoseturn.allowedattackers - len(whoseturn.attacked)) + ' left).'

		# choose attacker on board.
		choice = choosefrom(units + abilities, msg=msg)
		if choice is None:
			if subphase is 3:
				break
			units = []
			update(subphase=3)
		elif isinstance(choice, Ability):
			if choice.canbuy:
				buy(choice)
			elif choice.canuse:
				use(choice)
			units = attackers(whoseturn)
		else:
			# choose target on board.
			target = choosefrom(choice.GetTargetCards(), msg='Choose target.')
			if target is None:
				continue

			#attack with choice.
			choice.attack(target)
			update(subphase=2)
			units = attackers(whoseturn)

		abilities = availableabilities()

	nextphase()


# build magic phase.
def magicphase():
	update(subphase=1)
	cards = whoseturn.hand
	abilities = availableabilities()
	while subphase < 3 or not isempty(abilities):
		if subphase is 3:
			msg = 'Abilities available.'
		else:
			msg = 'Choose card to convert to magic.'

		# choose card to convert to magic.
		choice = choosefrom(cards + abilities, msg=msg)
		if choice is None:
			if subphase is 3:
				break
			cards = []
			update(subphase=3)
		elif isinstance(choice, Ability):
			if choice.canbuy:
				buy(choice)
			elif choice.canuse:
				use(choice)
		else:
			# move it to magic pile.
			move(choice, whoseturn.magicpile)
			update(subphase=2)

		abilities = availableabilities()

	nextphase()


def refreshphase():
	global justloaded, whoseturn

	#undo modifiers (or refreshing will mess up stats).
	for mod in modifiers.copy():
		if mod.turns <= 0:
			mod.undo()
			remove(mod, modifiers)

	#save turn. Note that the whoseturn has not actually changed yet.
	global justloaded
	if not justloaded:
		saveturn()
	justloaded = False

	#decrement modifier turns left.
	for mod in modifiers:
		mod.turns -= 1
	for mod in gamemods.copy():
		mod.turns -= 1

	# refresh units so they can move, attack, etc. again.
	for unit in whoseturn.deck.units:
		unit.refresh()

	#set next turn to be next summoner's.
	whoseturn = summoners[(summoners.index(whoseturn) + 1) % len(summoners)]
	print("\n===" + name(whoseturn) + "'s Turn===")

	nextphase()


# go to next 
def nextphase():
	global phase
	phase = PHASES[(PHASES.index(phase) + 1) % len(PHASES)]
	phase()


# -----------------------------------Card classes---------------------------------------
class Faction:
	'''Path to folder to search for pictures:
	 	symbol-lrg.png for logo.
	 	prefix-name.jpg for card pic based on type: evt, com, chm, ref as prefixes. cardback.jpg for card back.
	 	name.png for in-game semitransparent picture.
	'''
	path = ''
	summonerclasses = []
	commonclasses = []
	championclasses = []


# deck is a list with certain card constraints on its contents.
class Deck(list):
	def __init__(self, summoner, commons, champions, walls):
		assert len(commons) is 18
		assert len(champions) is 3
		assert len(walls) is 3

		super().__init__()

		self.walls = walls
		self.summoner = summoner
		self.commons = commons
		self.champions = champions
		self.events = summoner.events
		self.units = commons + champions + [summoner]

		extend(self, self.walls + self.units + summoner.events)


# card
# possible statuses: drawpile, magicpile, inhand, summoned, moved, attacked, destroyed
class Card(object):
	def __init__(self, owner, cardpicpath, faction):
		self.pos = None
		self.owner = owner
		self.cardpicpath = cardpicpath
		self.faction = faction


# events temporarily mod attributes of cards and are usually played during event phase.
class Event(Card):
	def __init__(self, owner, desc, faction, cost=0, discardonuse=True):
		self.discardonuse = discardonuse
		self.cost = cost
		self.desc = desc
		super().__init__(owner=owner, cardpicpath=faction.path + r'\evt-' + self.__class__.__name__ + '.jpg', faction=faction)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return whoseturn is self.owner and phase is eventphase

	def use(self, whoseturn, phase, subphase, action, subaction):
		pass


# summonable unit has attributes like life and cost and methods like move and attack.
class Unit(Card):
	def __init__(self, owner, atk, range, maxlife, cost, cardpicpath, faction):
		super().__init__(owner, cardpicpath, faction=faction)
		self.picpath = faction.path + "\\" + self.__class__.__name__ + '.png'  # in-game image for Units
		self.cost = cost
		self.atk = atk
		self.range = range
		self.maxlife = maxlife
		self.life = maxlife
		self.movesleft = DEFAULT_MOVES
		self.attacksleft = DEFAULT_ATTACKS
		self.abilities = []

	def refresh(self):
		for ability in self.abilities:
			ability.refresh()
		self.movesleft = DEFAULT_MOVES
		self.attacksleft = DEFAULT_ATTACKS

	# move to a cell and decrement number of moves by 1.
	def move(self, cell):
		return execute(Move(self, cell))

	#wound a target without deducting from attacksleft. Return successfully wounded total.
	def wound(self, target, numwounds=1):
		return execute(Wound(self, target, numwounds))

	#attacking makes an attack object, decrements attacks left, makes target take damage, and cleans target up if killed it.
	def attack(self, target):
		return execute(Attack(self, target))

	#get cells that self can be summoned onto.
	def getsummoncells(self):
		return execute(GetSummonCells(self))

	#get cells that self can move to.
	def getmovecells(self):
		return execute(GetMoveCells(self))

	#roll a certain number of times for whatever reason.
	def roll(self, times):
		return execute(Roll(roller=self, numdice=times))

	#get targets for self. if not given, set to range attribute's value.
	def GetTargetCards(self, range=None):
		r = self.range
		if range is not None:
			r = range
		return execute(GetTargetCards(self, r))


# walls are cards you can summon next to.
class Wall(Event):
	def __init__(self, owner, faction):
		super().__init__(owner, faction=faction, desc='Summoning point.', discardonuse=False)
		self.picpath = faction.path + "\\" + self.__class__.__name__ + '.png'
		self.maxlife = 9
		self.life = self.maxlife

	def use(self, whoseturn, phase, subphase, action, subaction):
		cell = choosefrom(cellsonboard(onlyempties=True, team=self.owner.team), msg='Choose a cell to place wall.')
		if cell is None:
			return False

		move(self, cell)
		return True


# summoners are the players themselves.
class Summoner(Unit):
	def __init__(self, atk, range, maxlife, events, setupdict, faction):
		assert len(events) is 9
		super().__init__(owner=self, atk=atk, range=range, maxlife=maxlife, cost=0, cardpicpath=faction.path + r'\sum-' + self.__class__.__name__ + '.jpg', faction=faction)
		self.events = events
		self.setupdict = setupdict  #this is the starting card setup having coordinates : cardclass
		self.drawpile = Stack()
		self.discardpile = Stack()
		self.magicpile = Stack()
		self.hand = Stack()

		self.moved = []
		self.attacked = []

		self.allowedmovers = DEFAULT_MOVERS
		self.allowedattackers = DEFAULT_ATTACKERS
		self.allowedinhand = DEFAULT_DRAWS

	#this refresh method also clears list of moved and attacked this turn.
	def refresh(self):
		Unit.refresh(self)
		self.moved = []
		self.attacked = []

	#draw card.
	def draw(self):
		move(top(self.drawpile), self.hand)

	#discard card.
	def discard(self, card):
		move(card, self.discardpile)

	#summon a unit.
	def summon(self, unit, pos, free=False):
		assert free or len(self.magicpile) >= unit.cost
		execute(Summon(self, unit, pos, free))

	#play an event card.
	def playevent(self, event):
		assert event in self.hand
		return execute(PlayEvent(self, event))

	# add self to team and put starting cards on board using setup dictionary given from implementing class.
	def setup(self, playernum, deck, team, enemyteam):
		self.deck = deck
		self.playernum = playernum
		self.team = team
		add(self, team)
		self.enemyteam = enemyteam

		# put all cards but summoner in draw pile.
		extend(self.drawpile, self.deck)
		for card in self.drawpile:
			card.pos = self.drawpile

		#put starting cards on board.
		for x in range(6):
			for y in range(4):
				if (x + 1, y + 1) in self.setupdict:
					found = False
					for card in self.drawpile:  #look for matching card in drawpile
						if card.__class__ is self.setupdict[(x + 1, y + 1)]:
							if self.playernum is 0:
								move(card, board[x][y])
							elif self.playernum is 1:
								move(card, board[5 - x][7 - y])
							elif self.playernum is 2:
								move(card, board[11 - x][7 - y])
							elif self.playernum is 3:
								move(card, board[6 + x][y])

							found = True
							break
					assert found, 'Setup card ' + str(self.setupdict[(x + 1, y + 1)]) + ' not found in draw pile.'

				# shuffle the pile.
				shuffle(self.drawpile)


# basic unit.
class Common(Unit):
	def __init__(self, owner, atk, range, cost, maxlife, faction):
		super().__init__(owner=owner, atk=atk, range=range, cost=cost, maxlife=maxlife, cardpicpath=faction.path + r'\com-' + self.__class__.__name__ + '.jpg', faction=faction)


# powerful unit.
class Champion(Unit):
	def __init__(self, owner, atk, range, cost, maxlife, faction):
		super().__init__(owner=owner, atk=atk, range=range, cost=cost, maxlife=maxlife, cardpicpath=faction.path + r'\chm-' + self.__class__.__name__ + '.jpg', faction=faction)