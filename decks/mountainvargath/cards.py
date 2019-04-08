from summonerwars.abilities import KnockAround, Trample
from summonerwars.decks.mercenaries.cards import Magos
from summonerwars.menus import *

# **********************************ABILITIES***************************************



class BattleFrenzy(Ability):
	def __init__(self, wielder):
		desc = "+1 atk when on enemy's side of field."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if self.wielder.pos in cellsonboard(team=self.wielder.owner.enemyteam):
			OffsetMod(self.wielder, attname='atk', offset=+1)


class CallLightning(Ability):
	def __init__(self, wielder):
		desc = "Wound self by 1 and an adjacent Unit by 2 instead of attacking."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3 and canattack(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose unit.
		unit = choosefrom(cardsfrom(self.wielder, spaces=1, type=Unit), msg="Choose an adjacent unit.")
		if unit is None:
			return False

		# wound it by 2.
		self.wielder.wound(unit, numwounds=2)

		#wound self by 1.
		self.wielder.wound(self.wielder)

		#decrement attacksleft.
		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)


class ChainLightning(Ability):
	def __init__(self, wielder):
		desc = "can attack again."
		super().__init__(wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		self.wielder.attacksleft += 1


class Command(Ability):
	def __init__(self, wielder):
		desc = "+1 atk to every controlled Common Mountain Vargath up to 2 spaces away from wielder."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		for unit in cardsfrom(self.wielder, spaces=2, owners=[self.wielder.owner], type=Common, faction=MountainVargath):
			OffsetMod(unit, attname='atk', offset=+1)


class DisruptionField(Ability):
	def __init__(self, wielder):
		desc = "All enemy units that begin a turn within 3 spaces of wielder have no ability and cannot gain an ability during that turn."
		super().__init__(wielder, desc=desc)
		self.affected = None

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn in self.wielder.owner.enemyteam and phase is drawphase and subphase is 1:
			self.affected = cardsfrom(self.wielder, spaces=3, owners=[whoseturn], type=Unit)

		if self.affected is not None:
			for unit in self.affected:
				Mod(unit, attname='abilities', value=[])
			# TODO: enemies may accidentally try to add ability to unit and it will be removed instead of them being warned

	def refresh(self):
		super().refresh()
		self.affected = None


class Emboldened(Ability):
	def __init__(self, wielder):
		desc = "+1 atk for each adjacent friendly Mountain Vargath Unit."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='atk', offset=+len(cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.team, faction=MountainVargath, type=Unit)))


class FallBackAbility(Ability):
	def __init__(self, wielder):
		super().__init__(wielder, desc='Allows wielder to choose a wall at end of turn to move controlled Summoner and 2 controlled Commons next to it.')

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is magicphase and subphase is 3

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose wall.
		wall = choosefrom(cardsonboard(type=Wall, owners=[self.wielder.owner]), msg='Choose a controlled wall.')

		# choose cell to move summoner.
		cell = choosefrom(cellsfrom(wall, spaces=1, onlyempties=True), msg='Choose a cell next to wall.')
		move(self.wielder.owner, cell)

		# choose up to 2 commons, given enough spaces.
		moved = []
		while len(moved) < 2:
			common = choosefrom([card for card in cardsonboard(owners=[self.wielder.owner], type=Common) if card not in moved], msg='Choose a controlled Common on board.')
			if common is None:
				return not isempty(moved)

			cell = choosefrom(cellsfrom(wall, spaces=1, onlyempties=True), msg='Choose a cell next to wall.')
			if cell is None:
				continue

			move(common, cell)
			add(common, moved)


class GreaterCommandAbility(Ability):
	def __init__(self, wielder):
		desc = '+1 atk to every controlled Common Mountain Vargath within 4 spaces from wielder.'
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		for unit in cardsfrom(self.wielder, spaces=4, owners=[self.wielder.owner], type=Common):
			OffsetMod(unit, attname='atk', offset=+1)


class Retribution(Ability):
	def __init__(self, wielder):
		desc = "When wielder is attacked by an adjacent unit, if wielder not destroyed, attacker gets wounded by 1 on a die roll of > 2."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.target is self.wielder and isadjacent(self.wielder, action.agent) and self.wielder.life > 0:
			roll = self.wielder.roll(1)
			if roll[0] > 2:
				self.wielder.wound(action.agent)


class Rush(Ability):
	def __init__(self, wielder):
		desc = "+2 moves if began to move on your side of the field during your movement phase."
		super().__init__(wielder, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		# deactivate if not owner's movement phase.
		if phase is not movephase or whoseturn is not self.wielder.owner:
			self.activated = False


		else:
			# if the +2 movesleft was already partly used, keep it.
			if self.activated:
				OffsetMod(self.wielder, attname='movesleft', offset=+2)

			# activate if wielder hasn't moved and is on his side of the field.
			else:
				if self.wielder not in self.wielder.owner.moved:
					for cell in cellsonboard(team=self.wielder.owner.team):
						if self.wielder in cell:
							OffsetMod(self.wielder, attname='movesleft', offset=+2)
							self.activated = True


class Steadfast(Ability):
	def __init__(self, wielder):
		desc = "Attacks against wielder can only wound him by 1 if wielder is next to an enemy wall with < 4 life."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 2 and action.numhits > 1 and len([wall for wall in cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam, type=Wall) if wall.life < 4]) > 0:
			action.numhits = 1


class SunderHammer(Ability):
	def __init__(self, wielder):
		desc = "use at: turn end\n\neffect: Wound a wall next to wielder by 2."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is magicphase and len(cardsfrom(self.wielder, spaces=1, type=Wall)) > 0

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose wall.
		wall = choosefrom(cardsfrom(self.wielder, spaces=1, type=Wall), msg='Choose a wall next to ' + name(self.wielder) + '.')
		if wall is None:
			return False

		# wound it by 2.
		self.wielder.wound(wall, numwounds=2)


# **********************************EVENTS***************************************
class Muster(Event):
	def __init__(self, owner, faction):
		desc = "Move up to 2 controlled Commons next to your Summoner."
		super().__init__(owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		moved = []

		while len(moved) < 2:
			# get common not moved yet.
			common = choosefrom([card for card in cardsonboard(owners=[self.owner], type=Common) if card not in moved], msg='Choose a controlled Common.')
			if common is None:
				return not isempty(moved)

			# get cell next to summoner.
			cell = choosefrom(cellsfrom(self.owner, spaces=1, onlyempties=True), msg='Choose a cell next to summoner.')
			if cell is None:
				continue

			# move there.
			move(common, cell)

			add(common, moved)


class SuperiorPlanning(Event):
	def __init__(self, owner, faction):
		desc = "Put a Sunderved event card from either your draw pile or discard pile into your hand and shuffle your draw pile."
		super().__init__(owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		lst = [card for card in self.owner.drawpile if card in self.owner.deck.events] + [card for card in self.owner.discardpile if card in self.owner.deck.events]
		event = choosefrom(lst, msg='Choose Sunderved event from your draw or discard pile.')
		if event is None:
			return False

		move(event, self.owner.hand)
		shuffle(self.owner.drawpile)


class FallBack(Event):
	def __init__(self, owner, faction):
		desc = "Move your Summoner and 2 controlled Commons next to a controlled Wall at the end of your turn."
		super().__init__(owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		ListAddMod(self.owner.abilities, element=FallBackAbility(self.owner), turns=1)


class GreaterCommand(Event):
	def __init__(self, owner):
		desc = "Move up to 2 controlled Commons next to your Summoner."
		super().__init__(owner, desc=desc, faction=MountainVargath)

	def use(self, whoseturn, phase, subphase, action, subaction):
		ListAddMod(self.owner.abilities, element=GreaterCommandAbility(self.owner), turns=1)


class TorodinsAdvance(Event):
	def __init__(self, owner):
		desc = "Torodin can move 2 more spaces during next move phase."
		super().__init__(owner, desc=desc, faction=MountainVargath)

	def use(self, whoseturn, phase, subphase, action, subaction):
		for card in self.owner.deck.champions:
			if isinstance(card, Torodin):
				OffsetMod(card, attname='movesleft', offset=+2, turns=1)


# **********************************COMMONS***************************************

class Brute(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=3, faction=MountainVargath)
		KnockAround(wielder=self)


class StormMage(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=2, faction=MountainVargath)
		CallLightning(wielder=self)


class Warrior(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=MountainVargath)
		BattleFrenzy(wielder=self)


class Rusher(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=MountainVargath)
		Rush(wielder=self)


class Warden(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=3, faction=MountainVargath)
		Steadfast(wielder=self)


# **********************************CHAMPIONS***************************************

class Bellor(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=6, maxlife=7, faction=MountainVargath)
		Retribution(wielder=self)


class Growden(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=1, cost=6, maxlife=6, faction=MountainVargath)
		SunderHammer(wielder=self)


class Luka(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=7, maxlife=6, faction=MountainVargath)
		DisruptionField(wielder=self)


class Quen(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=5, maxlife=4, faction=MountainVargath)
		ChainLightning(wielder=self)


class Torodin(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=6, maxlife=7, faction=MountainVargath)
		Trample(wielder=self)


class Varn(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=5, maxlife=5, faction=MountainVargath)
		Emboldened(wielder=self)


# **********************************SUMMONERS***************************************

class Sunderved(Summoner):
	def __init__(self):
		setupdict = {(1, 4): Warrior, (2, 2): Brute, (3, 3): Wall, (4, 4): Rusher, (5, 3): Warrior, (4, 2): Sunderved}
		events = [Muster(self, faction=MountainVargath) for count in range(3)] + [GreaterCommand(self) for count in range(2)] + [SuperiorPlanning(self, faction=MountainVargath) for count in range(2)] + [TorodinsAdvance(self) for count in range(1)] + [FallBack(self, faction=MountainVargath) for count in range(1)]
		super().__init__(atk=3, range=1, maxlife=7, events=events, setupdict=setupdict, faction=MountainVargath)
		Command(wielder=self)


# **********************************FACTION***************************************
class DefaultMountainVargathDeck(Deck):
	def __init__(self):
		summoner = Sunderved()
		walls = [Wall(summoner, faction=MountainVargath) for count in range(3)]
		commons = [Warrior(summoner) for count in range(10)] + [StormMage(summoner) for count in range(5)] + [Rusher(summoner) for count in range(2)] + [Brute(summoner) for count in range(1)]
		champions = [Quen(summoner), Varn(summoner), Torodin(summoner)]
		super().__init__(summoner=summoner, commons=commons, champions=champions, walls=walls)


class MountainVargath(Faction):
	path = r'decks\mountainvargath\pics'
	commonclasses = [Brute, StormMage, Warrior, Rusher, Warden]
	championclasses = [Bellor, Growden, Luka, Quen, Torodin, Varn]
	summonerclasses = [Sunderved]


defaultdeckclasses[MountainVargath] = DefaultMountainVargathDeck
add(MountainVargath, factions)