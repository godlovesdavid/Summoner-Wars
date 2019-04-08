from summonerwars.menus import *

class Escape(Ability):
	# cost: 1
	# buy at: wielder has attacked
	# use at: ""
	# effect: move wielder up to 2 cells.
	def __init__(self, wielder):
		desc = "buy at: wielder has attacked\n\neffect: move up to 2 cells."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.wielder in self.wielder.owner.attacked

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		self.wielder.movesleft += 2
		cell = choosefrom(cellsfrom(self.wielder, spaces=2, onlyempties=True), msg='Choose a cell.')
		if cell is None:
			return False

		self.wielder.move(cell)


class Flight(Ability):
	def __init__(self, wielder):
		super().__init__(wielder, desc='Can move over cards, but must end move on unoccupied space.')

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is GetMoveCells and subaction is 2 and action.agent is self.wielder:
			action.lst = cellsfrom(self.wielder, spaces=self.wielder.movesleft, onlyreachables=False, onlyempties=True)


class GreaterFlight(Ability):
	def __init__(self, wielder):
		desc = "+1 moves. Move through."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='movesleft', offset=+1)

		# move through.
		if type(action) is GetMoveCells and subaction is 2 and action.agent is self.wielder:
			action.lst = cellsfrom(self.wielder, spaces=self.wielder.movesleft, onlyreachables=False, onlyempties=True)


class KnockAround(Ability):
	# use at: wounded a unit
	# effect: move wounded unit up to 3 clear line spaces.
	def __init__(self, wielder):
		desc = "use at: wounded a unit\n\neffect: move wounded unit up to 3 clear line spaces."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Wound and subaction is 3 and action.agent is self.wielder and action.count > 0 and action.target.life > 0 and isinstance(action.target, Unit) and not isempty(straightlinecellsfrom(action.target, spaces=1, onlyempties=True)):
			cell = choosefrom(straightlinecellsfrom(action.target, spaces=3, onlyempties=True), msg='Choose a cell up to 3 clear line cells from target.')
			if cell is None:
				return True

			move(action.target, cell)


class Precise(Ability):
	def __init__(self, wielder):
		desc = "Attacking Units wounds them directly instead of rolling."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and isinstance(action.target, Unit):
			def render():
				action.numhits = self.wielder.atk
			action.render = render


class Rider(Ability):
	def __init__(self, wielder):
		desc = "Can move up to 7 spaces instead of moving normally."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase and subphase < 3 and self.wielder not in self.wielder.owner.moved

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose cell.
		cell = choosefrom(straightlinecellsfrom(self.wielder, spaces=7, onlyempties=True), 'Choose a space to move to.')
		if cell is None:
			return False

		#move there.
		self.wielder.move(cell)


class Swift(Ability):
	def __init__(self, wielder):
		desc = "+1 moves."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='movesleft', offset=+1)


class Trample(Ability):
	def __init__(self, wielder):
		desc = "Can move through Commons. Each moved through gets 1 wound. Must end movement on unoccupied cell."
		super().__init__(wielder, desc=desc)

	# num moves left must be > 1 so that we can move off it after. TODO: should also be able to use if somehow can move not in the movement phase
	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase and self.wielder.movesleft >= 2 and (len(self.wielder.owner.moved) < self.wielder.owner.allowedmovers or self.wielder in self.wielder.owner.moved) and not isempty(cardsfrom(self.wielder, spaces=1, type=Common))

	def use(self, whoseturn, phase, subphase, action, subaction):
		wounded = False

		#while not on an empty cell:
		while len(self.wielder.pos) > 1 or not wounded:
			#choose a cell to move to.
			cell = choosefrom([cell for cell in cellsfrom(self.wielder, spaces=1, onlyempties=False) if isempty(cell) or (isinstance(top(cell), Common) and (top(cell).life is 1 or self.wielder.movesleft >= 2))], 'Choose a cell to move to.')

			#move there.
			self.wielder.move(cell)

			#wound common in cell.
			for card in self.wielder.pos:
				if card is not self.wielder and isinstance(card, Common):
					self.wielder.wound(card)
			wounded = True #first wound was needed to start loop

		return False #allow doing it again