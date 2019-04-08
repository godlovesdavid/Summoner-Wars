from summonerwars.menus import *
from summonerwars.abilities import Swift, Rider

# **********************************ABILITIES***************************************

class Assault(Ability):
	def __init__(self, wielder):
		desc = "Can attack all adjacent units at one time."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.agent is self.wielder and len(cardsfrom(self.wielder, spaces=1)) > 0:
			attacked = [action.target]

			availabletargets = [card for card in cardsfrom(self.wielder, spaces=1) if card not in attacked]
			while len(availabletargets) > 0:

				target = choosefrom(availabletargets, msg='Choose another adjacent card to attack.')
				if target is None:
					return False

				# change attack obj so that it doesn't decrement attacksleft.
				attack = Attack(self.wielder, target)

				def apply():
					attack.wound = Wound(action.agent, attack.target, attack.numhits)
					execute(attack.wound)

				attack.apply = apply
				execute(attack)

				add(target, attacked)
				availabletargets = [card for card in cardsfrom(self.wielder, spaces=1) if card not in attacked]

			clear(attacked)


class OutOfShadows(Ability):
	def __init__(self, wielder):
		desc = "+2 atk while attacking an adjacent unit if began turn adjacent to an enemy unit."
		super().__init__(wielder, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner and phase is drawphase and subphase is 1 and not isempty(cardsfrom(self.wielder, spaces=1, type=Unit, owners=self.wielder.owner.enemyteam)):
			self.activated = True
			print(name(self.wielder.owner) + "'s OutOfShadows activated (+2 atk against an adjacent unit).")
		elif self.activated and type(action) is Attack and subaction is 3 and action.agent is self.wielder and isinstance(action.target, Unit) and isadjacent(action.target, self.wielder):
			def render():
				action.agent.atk += 2
				Attack.render(action)
				action.agent.atk -= 2

			action.render = render
			self.activated = False


class ReturnSpirit(Ability):
	def __init__(self, wielder):
		desc = "use at: your turn end\n\neffect: return an adjacent Common back to its summoner's hand (healing it back up and discarding all its held cards)."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is magicphase and subphase is 3 and len(cardsfrom(self.wielder, spaces=1, type=Common)) > 0

	def use(self, whoseturn, phase, subphase, action, subaction):
		common = choosefrom(cardsfrom(self.wielder, spaces=1, type=Common), msg="Choose an adjacent common.")
		if common is None:
			return False

		common.life = common.maxlife
		move(common, common.owner.hand)

	# TODO: discard held cards


class ScoutAbility(Ability):
	def __init__(self, wielder):
		desc = "+1 allowed movers during move phase if wielder is on enemy's side of field at your turn begin."
		super().__init__(wielder, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner:
			if phase is drawphase and subphase is 1:
				for cell in cellsonboard(team=self.wielder.owner.enemyteam):
					for card in cell:
						if card is self.wielder:
							self.activated = True
							print('Scout lets you move an extra unit.')
							return
			elif phase is movephase:
				if self.activated:
					OffsetMod(self.wielder.owner, attname='allowedmovers', offset=+1, turns=1)
					self.activated = False
					return True


class ShadowArrows(Ability):
	def __init__(self, wielder):
		desc = "Once per turn, when destroyed a unit, can move there and attack again."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		# see if wielder killed a unit.
		if type(action) is Attack and subaction is 3 and self.wielder is action.agent and isinstance(action.target, Unit) and action.target.life <= 0:
			# move there if desired.
			cell = choosefrom([action.startcell], msg="You may move to the destroyed unit's position.")
			if cell is not action.startcell:
				return False

			move(self.wielder, action.startcell)

			#allow another attack.
			self.wielder.attacksleft += 1
			return True


class ShadowDancer(Ability):
	def __init__(self, wielder):
		desc = "Can choose to ignore one of the dice rolled for the attack the first time wielder is attacked on a turn."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 2 and action.target is self.wielder:
			die = choosefrom(action.rolllist, msg=name(self.wielder.owner) + ', choose an die to ignore.')
			if die is None:
				return # can only use on first attack

			del action.rolllist[action.rolllist.index(die)]
			if action.numhits > 0 and die >= action.rolltohit:
				action.numhits -= 1
			print('Ignored', die)
			return True


class ShadowStep(Ability):
	used = []  # for remembering summoners who used a ShadowStep

	def __init__(self, wielder):
		desc = "Can summon wielder next to a controlled Shadow Elf Unit. Shadow Step can only ever be activated once per turn."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is GetSummonCells and subaction is 2 and action.agent is self.wielder and self.wielder.owner not in ShadowStep.used:
			for card in cardsonboard(owners=[self.wielder.owner], type=Unit, faction=ShadowElves):
				action.lst += cellsfrom(card, spaces=1, onlyempties=True)

		elif type(action) is Summon and subaction is 3 and action.target is self.wielder:
			add(action.agent, ShadowStep.used)

	def refresh(self):
		super().refresh()
		remove(self.wielder.owner, ShadowStep.used)


class Sneak(Ability):
	def __init__(self, wielder):
		desc = "+2 moves if wielder is the only one moving during move phase."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase and subphase < 3 and (isempty(self.wielder.owner.moved) or len(self.wielder.owner.moved) is 1 and self.wielder in self.wielder.owner.moved)

	def use(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='movesleft', offset=+2, turns=1)
		Mod(self.wielder.owner, attname='allowedmovers', value=1, turns=1)
		cell = choosefrom(self.wielder.getmovecells(), msg='Choose a cell to move to.')
		if cell is None:
			return True
		self.wielder.move(cell)


class SwiftStrike(Ability):
	def __init__(self, wielder):
		desc = "+1 attacks left after attacking."
		super().__init__(wielder, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.agent is self.wielder:
			self.activated = True

		# if player did anything after wielder's attack (used non-autouse ability, attacked, changed phase), disable ability.
		if subaction is 3:
			self.activated = False

		if self.activated:
			OffsetMod(self.wielder, attname='attacksleft', offset=+1)


class SummonTheNightAbility(Ability):
	def __init__(self, wielder, chosenopponent):
		desc = "Chosen opponent can only move his units 1 space each during his movement phase and can only attack adjacent units during his attack Phase."
		super().__init__(wielder, desc=desc)
		self.chosenopponent = chosenopponent

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.chosenopponent:
			# can only move 1 cell.
			if phase is movephase:
				if type(action) is GetMoveCells and subaction is 1:
					def render():
						action.lst = cellsfrom(action.agent, spaces=1, onlyempties=True)

					action.render = render
				if type(action) is Move and subaction is 1:
					def render():
						action.count = action.agent.movesleft

					action.render = render

			#can only attack up to 1 range.
			if phase is attackphase:
				if type(action) is GetTargetCards and subaction is 2:
					if action.agent.owner is self.chosenopponent:
						for card in action.lst.copy():
							if not isadjacent(card, action.agent):
								remove(card, action.lst)


class Wither(Ability):
	def __init__(self, wielder):
		desc = "Must pay 1 magic point every time wielder destroyed no unit during an attack phase, else wound your summoner by 1."
		super().__init__(wielder, desc=desc)
		self.numdestroyed = 0

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		# count num destroyed.
		if whoseturn is self.wielder.owner:
			if phase is attackphase and type(action) is Attack and subaction is 3 and action.agent is self.wielder and action.target.life <= 0:
				return True

			#if got this far without returning True, didn't kill anything.
			if phase is attackphase and subphase is 3:
				if isempty(self.wielder.owner.magicpile):
					self.wielder.wound(self.wielder.owner)
					print(name(self.wielder) + "'s withering wounded " + name(self.wielder.owner))
				else:
					choice = choosefrom(['wound', 'pay'], msg=name(self.wielder) + " didn't kill anything. pay or wound?")
					while choice != 'pay' or choice != 'wound':
						if choice == 'pay':
							self.wielder.owner.discard(top(self.wielder.owner.magicpile))
							print(name(self.wielder) + "'s withering costed " + name(self.wielder.owner) + " 1 magic.")
						else:
							self.wielder.wound(self.wielder.owner)
							print(name(self.wielder) + "'s withering wounded " + name(self.wielder.owner))
				return True


# **********************************EVENTS***************************************

class IntoDarkness(Event):
	def __init__(self, owner):
		desc = "Discard up to 2 of an opponent's Commons if they cost < 3 and that opponent has less units than you."
		super().__init__(owner, cost=0, desc=desc, faction=ShadowElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose opponent with less units.
		opponent = choosefrom([summoner for summoner in self.owner.enemyteam if len(cardsonboard(owners=[summoner], type=Unit)) > len(cardsonboard(owners=[self.owner], type=Unit))], msg="Choose an opponent with more units than you.")
		if opponent is None:
			return False

		chosen = []
		while len(chosen) < 2:
			common = choosefrom([card for card in cardsonboard(owners=[opponent], type=Common) if card.cost < 3], 'Choose a unit with cost of 2 or less.')
			if common is None:
				return len(chosen) > 0

			self.owner.discard(common)
			add(common, chosen)


class Shadows(Event):
	def __init__(self, owner):
		desc = "When one of your Commons or Champions would be put into an opponent's magic pile after being destroyed, put it in yours instead."
		super().__init__(owner, cost=0, desc=desc, faction=ShadowElves)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return type(action) is Wound and subaction is 3 and action.target.life <= 0 and action.target.owner is self.owner and action.target.faction is ShadowElves and (isinstance(action.target, Common) or isinstance(action.target, Champion)) and action.target.pos is action.agent.owner.magicpile

	def use(self, whoseturn, phase, subphase, action, subaction):
		move(action.target, self.owner.magicpile)
		print("Moved destroyed to " + name(self.owner) + "'s magic pile instead.")


class StalkingAdvance(Event):
	def __init__(self, owner):
		desc = "Move all controlled shadow elves up to 1 space each."
		super().__init__(owner, cost=0, desc=desc, faction=ShadowElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		moved = []

		# while there's still units you haven't moved,
		choices = cardsonboard(owners=[self.owner], faction=ShadowElves, type=Unit)
		while len(choices) > 0:
			# choose a unit you haven't moved.
			choice = choosefrom(choices, msg='Choose a unit to move.')
			if choice is None:
				return not isempty(moved)

			cell = choosefrom(cellsfrom(choice, spaces=1, onlyempties=True), msg='Choose a cell to move.')
			if cell is None:
				continue

			#move there.
			move(choice, cell)
			add(choice, moved)
			choices = [unit for unit in cardsonboard(owners=[self.owner], faction=ShadowElves, type=Unit) if unit not in moved]


class SummonTheNight(Event):
	def __init__(self, owner):
		desc = "A chosen opponent can move his units up to only 1 space each during his next move phase. He can also only attack adjacent units during his next attack phase."
		super().__init__(owner, cost=0, desc=desc, faction=ShadowElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		opponent = choosefrom(self.owner.enemyteam, msg='Choose an opponent.')
		if opponent is None:
			return False

		ListAddMod(self.owner.abilities, SummonTheNightAbility(self.owner, chosenopponent=opponent), turns=2)


# **********************************COMMONS***************************************
class Blademaster(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=2, faction=ShadowElves)
		SwiftStrike(wielder=self)


class Hunter(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=2, maxlife=1, faction=ShadowElves)
		ShadowStep(wielder=self)


class Scout(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=0, maxlife=1, faction=ShadowElves)
		ScoutAbility(wielder=self)


class Ranger(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=1, maxlife=1, faction=ShadowElves)
		ShadowArrows(wielder=self)


class Swordsman(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=1, maxlife=1, faction=ShadowElves)
		Swift(wielder=self)


# **********************************CHAMPIONS***************************************

class Hydrake(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=1, cost=8, maxlife=8, faction=ShadowElves)
		Assault(wielder=self)


class Kuldrid(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=3, cost=6, maxlife=6, faction=ShadowElves)
		Wither(wielder=self)


class Malidala(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=5, maxlife=3, faction=ShadowElves)
		ShadowDancer(wielder=self)


class Melek(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=1, cost=5, maxlife=5, faction=ShadowElves)
		Rider(wielder=self)


class Taliya(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=6, maxlife=5, faction=ShadowElves)
		ReturnSpirit(wielder=self)


class Xaserbane(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=1, cost=4, maxlife=4, faction=ShadowElves)
		Sneak(wielder=self)


# **********************************SUMMONERS***************************************

class Selundar(Summoner):
	def __init__(self):
		setupdict = {(1, 1): Ranger, (2, 2): Swordsman, (3, 4): Swordsman, (4, 2): Scout, (4, 3): Wall, (5, 2): Ranger, (6, 1): Selundar, (6, 3): Swordsman}
		events = [Shadows(self) for count in range(3)] + [IntoDarkness(self) for count in range(2)] + [StalkingAdvance(self) for count in range(2)] + [SummonTheNight(self) for count in range(2)]
		super().__init__(atk=2, range=3, maxlife=7, setupdict=setupdict, faction=ShadowElves, events=events)
		OutOfShadows(wielder=self)


# **********************************DECKS***************************************

class DefaultShadowElvesDeck(Deck):
	def __init__(self):
		summoner = Selundar()
		walls = [Wall(summoner, faction=ShadowElves) for count in range(3)]
		commons = [Swordsman(summoner) for count in range(10)] + [Scout(summoner) for count in range(3)] + [Ranger(summoner) for count in range(3)] + [Hunter(summoner) for count in range(2)]
		champions = [Xaserbane(summoner), Hydrake(summoner), Melek(summoner)]
		super().__init__(summoner, commons, champions, walls)


class ShadowElves(Faction):
	path = r'decks\shadowelves\pics'
	commonclasses = [Scout, Ranger, Swordsman, Hunter, Blademaster]
	championclasses = [Hydrake, Malidala, Xaserbane, Melek, Kuldrid, Taliya]
	summonerclasses = [Selundar]


defaultdeckclasses[ShadowElves] = DefaultShadowElvesDeck
add(ShadowElves, factions)