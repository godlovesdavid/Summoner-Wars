from summonerwars.abilities import *
from summonerwars.events import *


# **********************************ABILITIES***************************************
class BlazeDodge(Ability):
	def __init__(self, wielder):
		desc = "Commons or Champions attacking wielder who rolled a miss and not having destroyed wielder get wounded by 1. Wielder must move to a cell next to attacker."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.agent.owner.team is self.wielder.owner.enemyteam and action.target is self.wielder and len(['miss' for roll in action.rolllist if roll < action.rolltohit]) >= 1 and self.wielder.life > 0:
			self.wielder.wound(action.agent)
			while len(cellsfrom(action.agent, spaces=1, onlyempties=True)) > 0:
				cells = cellsfrom(action.agent, spaces=1, onlyempties=True)
				if self.wielder.pos in cellsfrom(action.agent, spaces=1, onlyempties=False):
					add(self.wielder.pos, cells)
				cell = choosefrom(cells, msg=name(self.wielder.owner) + ', choose a cell next to attacker to move ' + name(self.wielder))
				if cell is None:
					continue

				move(self.wielder, cell)


class BlazeStep(Ability):
	def __init__(self, wielder):
		desc = "Move next to a wall of yours at end of turn."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is magicphase and subphase is 3

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose a cell next to wall.
		cell = choosefrom(wallcells(self.wielder.owner), msg='Choose a cell next to a wall of yours.')
		if cell is None:
			return False

		# move there.
		move(self.wielder, cell)


class BlazingConscription(Ability):
	def __init__(self, wielder):
		desc = "At turn begin, take over control of Common or Champion that's next to wielder, til turn end."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is drawphase and subphase is 1

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom([card for card in cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam) if isinstance(card, Common) or isinstance(card, Champion)], 'Choose a Common or Champion next to ' + name(self.wielder))
		if choice is None:
			return False

		Mod(choice, attname='owner', value=self.wielder.owner, turns=1)


class BreathOfFlame(Ability):
	def __init__(self, wielder):
		desc = "Can wound all cards within 3 straght line spaces instead of attacking normally."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3 and canattack(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose cell.
		cell = choosefrom(straightlinecellsfrom(self.wielder, spaces=3, onlyreachables=False, includeowncell=True), msg='choose a cell.')
		if cell is None:
			return False

		# get all cells between here and there, inclusive.
		if self.wielder.pos.x > cell.x:
			dir = 'w'
		elif self.wielder.pos.x < cell.x:
			dir = 'e'
		elif self.wielder.pos.y > cell.y:
			dir = 's'
		elif self.wielder.pos.y < cell.y:
			dir = 'n'
		distance = abs(cell.x - self.wielder.pos.x) + abs(cell.y - self.wielder.pos.y)
		for card in straightlinecardsfrom(self.wielder, spaces=distance, directions=dir):
			# wound all cards in those cells.
			self.wielder.wound(card)

		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)


class BurningBlade(Ability):
	def __init__(self, wielder):
		desc = "Add 1 wound to attack."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.agent is self.wielder and action.target.life > 0:
			self.wielder.wound(action.target)


class FarShot(Ability):
	def __init__(self, wielder):
		desc = "+1 range."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='range', offset=+1)


class FireBlast(Ability):
	def __init__(self, wielder):
		desc = "Inflict 2 wounds on a card within 2 clear line cells, instead of attacking."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3 and canattack(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		card = choosefrom(self.wielder.GetTargetCards(range=2), msg='Choose a target to wound.')
		if card is None:
			return False

		self.wielder.wound(card, numwounds=2)

		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)


class HellFire(Ability):
	def __init__(self, wielder):
		desc = "Wound all adjacent units by 1 instead of attacking."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3 and canattack(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		for card in cardsfrom(self.wielder, spaces=1):
			self.wielder.wound(card)

		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)


class HeroicFlight(Ability):
	def __init__(self, wielder):
		super().__init__(wielder, desc='Can move over cards, but must end move on unoccupied space. Adjacent controlled Units with Heroic Flight get +1 atk. Adjacent controlled Units with Greater Flight get +2 atk.')

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		for card in cardsfrom(self.wielder, spaces=1, type=Unit):
			for ability in card.abilities:
				if isinstance(ability, HeroicFlight):
					OffsetMod(card, attname='atk', offset=+1)
				elif isinstance(ability, GreaterFlight):
					OffsetMod(card, attname='atk', offset=+2)
		if type(action) is GetMoveCells and subaction is 2 and action.agent is self.wielder:
			action.lst = cellsfrom(self.wielder, spaces=self.wielder.movesleft, onlyreachables=False, onlyempties=True)


class Pursue(Ability):
	def __init__(self, wielder):
		desc = "Move wielder to the cell a moving enemy Unit started moving when he moves away from having been adjacent to wielder. Roll and the mover gets 1 wound if roll > 4."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Move and subaction is 3 and isadjacent(self.wielder, action.startcell) and action.agent.owner in self.wielder.owner.enemyteam:
			# move wielder to the cell the mover just moved from.
			move(self.wielder, action.startcell)

			# roll and wound if roll is > 4.
			roll = self.wielder.roll(1)
			if roll[0] > 4:
				self.wielder.wound(action.agent)


class Riposte(Ability):
	def __init__(self, wielder):
		desc = "Units next to wielder that attack wielder get 1 wound if wielder is not destroyed by the attack."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.target is self.wielder and self.wielder.life > 0 and isadjacent(self.wielder, action.agent):
			self.wielder.wound(action.agent)


class SaveTheQueen(Ability):
	def __init__(self, wielder):
		desc = "Move 2 Common Phoenix Elves next to wielder at turn end."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is magicphase and subphase is 3

	def use(self, whoseturn, phase, subphase, action, subaction):
		moved = []
		while len(moved) < 2 and len(cellsfrom(self.wielder, spaces=1, onlyempties=True)) > 0:
			common = choosefrom([common for common in cardsonboard(owners=[self.wielder.owner], type=Common, faction=PhoenixElves) if common not in moved], msg="choose a controlled Common Phoenix Elf.")
			if common is None:
				return not isempty(moved)

			cell = choosefrom(cellsfrom(self.wielder, spaces=1, onlyempties=True), msg='Choose a cell next to ' + name(self.wielder))
			if cell is None:
				continue

			move(common, cell)
			add(common, moved)


class SmolderingEmbers(Ability):
	def __init__(self, wielder):
		desc = "+1 atk if no cards in your draw pile."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return isempty(self.wielder.owner.drawpile)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='atk', offset=+1)


class SummonFireBeast(Ability):
	def __init__(self, wielder):
		desc = "Summon fire beast from hand/drawpile next to wielder instead of attacking. Shuffle your draw pile"
		super().__init__(wielder, desc=desc, cost=2)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3 and canattack(self.wielder) and not isempty([card for card in self.wielder.owner.hand + self.wielder.owner.drawpile if isinstance(card, FireBeast)]) and len(cellsfrom(self.wielder, spaces=1, onlyempties=True)) > 0

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		firebeast = choosefrom([card for card in self.wielder.owner.hand + self.wielder.owner.drawpile if isinstance(card, FireBeast)], msg='Choose a Fire Beast from hand or drawpile.')
		if firebeast is None:
			return False

		cell = choosefrom(cellsfrom(self.wielder, spaces=1, onlyempties=True), msg='Choose a cell next to ' + name(self.wielder))
		if cell is None:
			return False

		move(firebeast, cell)
		shuffle(self.wielder.owner.drawpile)

		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)


class Thrust(Ability):
	def __init__(self, wielder):
		desc = "+1 atk if attacking an adjacent card."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and isadjacent(self.wielder, action.target):
			OffsetMod(self.wielder, attname='atk', offset=+1)


# **********************************EVENTS***************************************
class Burn(Event):
	def __init__(self, owner):
		desc = "Wound any Common or Champion."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom([card for card in cardsonboard(owners=self.owner.enemyteam) if isinstance(card, Champion) or isinstance(card, Common)], msg='Choose a Common or Champion to wound.')
		if choice is None:
			return False

		self.owner.wound(choice)


class ConjurePhoenixes(Event):
	def __init__(self, owner):
		desc = "Move up to 2 Phoenixes from your conjuration pile onto unoccupied spaces next to your summoner."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		used = False
		for count in range(2):
			cell = choosefrom(cellsfrom(self.owner, spaces=1, onlyempties=True), msg='Choose an unoccupied space next to your summoner to summon a Phoenix.')
			if cell is None:
				return used

			move(top(self.owner.conjurepile), cell)
			used = True


class GreaterBurn(Event):
	def __init__(self, owner):
		desc = "Wound any Common or Champion by 2."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom([card for card in cardsonboard(owners=self.owner.enemyteam) if isinstance(card, Champion) or isinstance(card, Common)], msg='Choose a Common or Champion to wound.')
		if choice is None:
			return False
		self.owner.wound(choice, numwounds=2)


class LavaFlow(Event):
	def __init__(self, owner):
		desc = "All units next to a controlled wall and the wall itself receive 1 wound. Draw 1 card."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		wall = choosefrom(cardsonboard(owners=[self.owner], type=Wall), msg='Choose a wall you control.')
		if wall is None:
			return False

		for card in cardsfrom(wall, spaces=1, type=Unit):
			self.owner.wound(card)

		self.owner.wound(wall)

		# draw 1 card.
		if not isempty(self.owner.drawpile):
			move(top(self.owner.drawpile), self.owner.hand)


class PassionOfThePhoenix(Event):
	def __init__(self, owner):
		desc = "All with Precise ability get +1 atk for 1 turn."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		for card in cardsonboard(owners=[self.owner], type=Unit):
			for ability in card.abilities:
				if isinstance(ability, Precise):
					OffsetMod(card, attname='atk', offset=+1, turns=1)


class ReleaseTheHounds(Event):
	def __init__(self, owner):
		desc = "Retrieve and reveal 3 cards of Fireling or Firebeast from your draw pile and shuffle it. Then you can magic magic and summon units, even next to your summoner."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# retrieve cards from draw pile.
		retrieved = []
		while len(retrieved) < 3:
			choice = choosefrom([card for card in self.owner.drawpile if isinstance(card, Fireling) or isinstance(card, FireBeast) and card not in retrieved], msg='Get 3 of Fireling and/or Firebeast from your draw pile.')
			if choice is None:
				break
			move(choice, self.owner.hand)
			add(choice, retrieved)
		shuffle(self.owner.drawpile)

		# let user make magic.
		while not isempty(self.owner.hand):
			choice = choosefrom([card for card in self.owner.hand if card is not self], msg='Choose card to convert to magic.')
			if choice is None:
				break
			move(choice, self.owner.magicpile)

		# let user summon things.
		while not isempty(self.owner.hand):
			choice = choosefrom(summonablecards(self.owner), msg='Choose a unit to summon.')
			if choice is None:
				break

			cell = choosefrom(choice.getsummoncells() + cellsfrom(self.owner, spaces=1, onlyempties=True), msg='Choose a cell next to a wall of yours or your summoner.')
			if cell is None:
				continue
			self.owner.summon(choice, cell)


class SpiritOfThePhoenix(Event):
	def __init__(self, owner):
		desc = "Choose a controlled Phoenix Elf Unit to gain Precise ability for 1 turn."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom(cardsonboard(owners=[self.owner], type=Unit), msg='Choose a controlled Phoenix Elf Unit.')
		if choice is None:
			return False

		ListAddMod(choice.abilities, element=Precise(choice), turns=1)


class WrathOfTheVolcano(Event):
	def __init__(self, owner):
		desc = "Wound a Common or Champion. Then discard up to 2 cards to wound it that many times again."
		super().__init__(owner, desc=desc, faction=PhoenixElves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# wound a unit.
		unit = choosefrom([card for card in cardsonboard(owners=self.owner.enemyteam, type=Unit) if isinstance(card, Common) or isinstance(card, Champion)], msg='Choose a Common or Champion.')
		if unit is None:
			return False
		self.owner.wound(unit)

		# discard up to twice to wound again.
		numdiscarded = 0
		while not isempty(self.owner.hand) and numdiscarded < 2 and unit.life > 0:
			choice = choosefrom([card for card in self.owner.hand if card is not self], 'Discard card to wound again (' + str(2 - numdiscarded) + ' left).')
			if choice is None:
				break

			self.owner.discard(choice)
			self.owner.wound(unit)

			numdiscarded += 1


# **********************************COMMONS***************************************

class Archer(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=1, maxlife=1, faction=PhoenixElves)
		FarShot(wielder=self)


class Fencer(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=0, maxlife=1, faction=PhoenixElves)
		Riposte(wielder=self)


class FireArcher(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=2, maxlife=1, faction=PhoenixElves)
		Precise(wielder=self)


class FireBeast(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=3, maxlife=3, faction=PhoenixElves)
		HellFire(wielder=self)


class FireDancer(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=3, maxlife=4, faction=PhoenixElves)
		BlazeDodge(wielder=self)


class Fireling(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=0, maxlife=1, faction=PhoenixElves)
		Pursue(wielder=self)


class Guardian(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=2, faction=PhoenixElves)
		Precise(wielder=self)


class Warrior(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=1, maxlife=1, faction=PhoenixElves)
		BlazeStep(wielder=self)


class Conjuration(Unit):
	def __init__(self, owner, atk, range, maxlife, faction):
		super().__init__(owner, atk=atk, range=range, maxlife=maxlife, cost=0, faction=PhoenixElves, cardpicpath=faction.path + r'\evt=' + self.__class__.__name__ + '.jpg')


class Phoenix(Conjuration):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, maxlife=1, faction=PhoenixElves)
		HeroicFlight(wielder=self)


# **********************************CHAMPIONS***************************************
class DukeRamazall(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=6, maxlife=6, faction=PhoenixElves)
		Precise(wielder=self)


class Fanessa(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=5, maxlife=5, faction=PhoenixElves)
		Riposte(wielder=self)


class FireDrake(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=1, cost=7, maxlife=7, faction=PhoenixElves)
		BreathOfFlame(wielder=self)


class Holleas(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=4, maxlife=5, faction=PhoenixElves)
		SummonFireBeast(wielder=self)


class Kaebeeros(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=3, range=1, cost=6, maxlife=6, faction=PhoenixElves)
		SmolderingEmbers(wielder=self)


class Kaeseeall(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=5, maxlife=5, faction=PhoenixElves)
		BlazingConscription(wielder=self)


class Laleya(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=5, maxlife=5, faction=PhoenixElves)
		Thrust(wielder=self)


class Maelena(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=5, maxlife=5, faction=PhoenixElves)
		BurningBlade(wielder=self)


class Rahlee(Champion):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=4, maxlife=4, faction=PhoenixElves)
		GreaterFlight(wielder=self)


# **********************************SUMMONERS***************************************

class PrinceElien(Summoner):
	def __init__(self):
		setupdict = {(1, 2): Warrior, (2, 3): Guardian, (3, 1): PrinceElien, (3, 3): Wall, (4, 1): Archer, (5, 2): Archer}
		spiritofthephoenixes = [SpiritOfThePhoenix(self) for count in range(3)]
		burns = [Burn(self) for count in range(2)]
		magicdrains = [MagicDrain(self, faction=PhoenixElves) for count in range(2)]
		greaterburns = [GreaterBurn(self) for count in range(1)]
		aheroisborns = [AHeroIsBorn(self, faction=PhoenixElves) for count in range(1)]
		events = spiritofthephoenixes + burns + magicdrains + greaterburns + aheroisborns
		super().__init__(atk=3, range=3, maxlife=4, events=events, setupdict=setupdict, faction=PhoenixElves)
		FireBlast(wielder=self)


class QueenMaldaria(Summoner):
	def __init__(self):
		setupdict = {(2, 3): Fireling, (2, 4): Fireling, (3, 3): Wall, (3, 2): QueenMaldaria, (4, 2): FireArcher, (5, 2): FireArcher, (6, 4): FireDancer}
		conjurephoenixes = [ConjurePhoenixes(self) for count in range(3)]
		passionofthephoenixes = [PassionOfThePhoenix(self) for count in range(2)]
		lavaflows = [LavaFlow(self) for count in range(2)]
		wrathofthevolcanoes = [WrathOfTheVolcano(self) for count in range(1)]
		releasethehoundses = [ReleaseTheHounds(self) for count in range(1)]
		events = conjurephoenixes + passionofthephoenixes + lavaflows + wrathofthevolcanoes + releasethehoundses
		super().__init__(atk=4, range=1, maxlife=4, events=events, setupdict=setupdict, faction=PhoenixElves)
		SaveTheQueen(wielder=self)


	# add special conjuration stuff.
	def setup(self, playernum, deck, team, enemyteam):
		self.deck.conjurations = [Phoenix(self) for count in range(6)]
		extend(self, self.deck.conjurations)
		self.deck.units.extend(self.deck.conjurations)

		self.conjurepile = Stack()
		super().setup(playernum, deck, team, enemyteam)
		for card in self.drawpile.copy():
			if isinstance(card, Conjuration):
				move(card, self.conjurepile)


# **********************************FACTION***************************************
class DefaultPhoenixElvesDeck(Deck):
	def __init__(self):
		summoner = PrinceElien()
		walls = [Wall(summoner, faction=PhoenixElves) for count in range(3)]
		commons = [Archer(summoner) for count in range(4)] + [Guardian(summoner) for count in range(1)] + [Fencer(summoner) for count in range(6)] + [Warrior(summoner) for count in range(7)]
		champions = [Maelena(summoner), FireDrake(summoner), Fanessa(summoner)]
		super().__init__(summoner, commons, champions, walls)


class PhoenixElves(Faction):
	path = r'decks\phoenixelves\pics'
	commonclasses = [Archer, Fencer, FireArcher, FireBeast, FireDancer, Fireling, Guardian, Warrior]
	championclasses = [DukeRamazall, Fanessa, FireDrake, Holleas, Kaebeeros, Kaeseeall, Laleya, Maelena, Rahlee]
	summonerclasses = [PrinceElien, QueenMaldaria]


defaultdeckclasses[PhoenixElves] = DefaultPhoenixElvesDeck
add(PhoenixElves, factions)