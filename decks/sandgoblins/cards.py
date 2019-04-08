from summonerwars.abilities import Escape, Flight
from summonerwars.menus import *

# **********************************ABILITIES***************************************
class BloodCraze(Ability):
	def __init__(self, wielder):
		desc = "+1 atk when attacking an already hurt Common or Champion."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and action.target.life < action.target.maxlife and isinstance(action.target, Common) or isinstance(action.target, Champion):
			def render():
				action.agent.atk += 1
				Attack.render(action)
				action.agent.atk -= 1
			action.render = render
			print('Bloodcraze added 1 atk.')


class Burrow(Ability):
	def __init__(self, wielder):
		desc = "+1 moves. Move through. When attacking, atk -1 for each space moved on current turn."
		super().__init__(wielder=wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#+1 moves.
		OffsetMod(self.wielder, attname='movesleft', offset=+1)

		#move through.
		if type(action) is GetMoveCells and subaction is 2 and action.agent is self.wielder:
			action.lst = cellsfrom(self.wielder, spaces=self.wielder.movesleft, onlyreachables=False, onlyempties=True)

		#atk -1 for each space moved on current turn.
		if type(action) is Move and subaction is 3 and action.agent is self.wielder:
			OffsetMod(self.wielder, attname='atk', offset=-action.distance, turns=1)

# let wielder cannot be attacked by non-adjacent units.
class Camouflage(Ability):
	def __init__(self, wielder):
		desc = "Cannot be attacked by nonadjacent Units."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is GetTargetCards and subaction is 3 and action.agent is not self.wielder and not isadjacent(self.wielder, action.agent):
			# take self off of nonadjacent units' targets.
			remove(self.wielder, action.lst)

class Conceal(Ability):
	def __init__(self, wielder):
		desc = "Choose a Common or Champion at your turn end to not let it attack wielder until your next turn begin."
		super().__init__(wielder=wielder, desc=desc)
		self.chosenunit = None

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner:
			#when expired.
			if phase is magicphase and subphase is 1:
				self.chosenunit = None

			#choosing a unit.
			if phase is attackphase and subphase is 3:
				self.chosenunit = choosefrom([card for card in cardsonboard(type=Unit)], msg='Choose a Common or Champion for ' + name(self.wielder) + ' to conceal from')

			#don't let it attack wielder.
			if type(action) is GetTargetCards and subaction is 3 and action.agent is self.chosenunit:
				remove(self.wielder, action)


class Cowardly(Ability):
	def __init__(self, wielder):
		desc = "If adjacent to an enemy unit at end of turn, roll and discard wielder on roll of 1-2."
		super().__init__(wielder, desc=desc)

	# discard wielder if enemy is next to wielder and rolled 1-2.
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner and phase is magicphase and subphase is 3 and len(cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam, type=Unit)) > 0:
			roll = self.wielder.roll(1)
			print(name(self.wielder), 'with the Cowardly ability rolled', roll[0])
			if roll[0] < 3:
				self.wielder.owner.discard(self.wielder)
				print('...and fled.')
			else:
				print('and decided to hold off the enemy some more.')
			return True # to prevent twice using in an update


class Crazed(Ability):
	def __init__(self, wielder):
		desc = 'Cannot move when adjacent to an enemy Unit.'
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if len(cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam, type=Unit)) > 0:
			Mod(self.wielder, attname='movesleft', value=0)


# switch places with an adjacent unit.
class Cunning(Ability):
	def __init__(self, wielder):
		desc = "You may exchange places with any adjacent Unit, once per your turn."
		super().__init__(wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return len(cardsfrom(self.wielder, spaces=1)) > 0

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom(cardsfrom(self.wielder, spaces=1, type=Unit), msg='Choose an adjacent Unit.')
		if choice is None:
			return False

		switchplaces(self.wielder, choice)

class Hasty(Ability):
	def __init__(self, wielder):
		desc = "Discard wielder if missed an attack. Wielder can attack again if rolled a 6 while attacking."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.agent is self.wielder:
			if not isempty([roll for roll in action.rolllist if roll < action.rolltohit]):
				self.wielder.owner.discard(self.wielder)
			elif 6 in action.rolllist:
				self.wielder.attacksleft += 1
				print(name(self.wielder), 'can attack again.')


class Lucky(Ability):
	def __init__(self, wielder):
		desc = "Can re-roll any chosen die, once per your turn."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner and type(action) is Roll and subaction is 2:
			die = choosefrom(action.lst, msg='Choose a die value to re-roll.')
			if die is None:
				return False

			del action.lst[action.lst.index(die)]
			add(randint(1, 6), action.lst)
			return True

class Sandstorm(Ability):
	def __init__(self, wielder):
		desc = "buy at: attack phase onwards\n\neffect: choose up to 3 Units within 3 spaces. Move each up to 1 space and roll a die for each. Wound each by 1 if roll is > 3."
		super().__init__(wielder, cost=2, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return (phase is attackphase or phase is magicphase)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		alreadymoved = []

		# get cards to move.
		while len(alreadymoved) < 3:
			# let user choose what unit to move.
			unit = choosefrom([unit for unit in cardsfrom(self.wielder, spaces=3, type=Unit, owners=self.wielder.owner.enemyteam) if unit not in alreadymoved], msg='Choose a unit to move.')
			if unit is None:
				return not isempty(alreadymoved)

			# get cells possible to move for unit to move.
			cell = choosefrom(cellsfrom(unit, spaces=1, onlyempties=True, includeowncell=True), msg='Choose a cell to move to.')
			if cell is None:
				continue

			move(unit, cell)

			roll = self.wielder.roll(1)
			if roll[0] > 3:
				print('Rolled', roll[0], '-- wounded', name(unit))
				self.wielder.wound(unit)
			else:
				print('Rolled', roll[0], '-- did not wound', name(unit))

			add(unit, alreadymoved)




# take damage by removing from scavenged if any.
class Scavenge(Ability):
	def __init__(self, wielder):
		desc = "Instead of discarding destroyed enemy, move it under self. When being attacked, discard one of those destroyed enemies to cancel all wounds from that attack."
		super().__init__(wielder, desc=desc)
		self.scavenged = []

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#killing something moves it under wielder.
		if type(action) is Wound and subaction is 3:
			attacking = action
			if attacking.agent is self.wielder and attacking.target.life <= 0:
				move(attacking.target, self.wielder.pos, index=self.wielder.pos.index(self.wielder))
				add(attacking.target, self.scavenged)
				print('Moved under', name(self.wielder))

		# if defending and has cards under, discard scavenged card.
		if type(action) is Wound and subaction is 2:
			wounding = action
			if wounding.target is self.wielder and wounding.count > 0 and not isempty(self.scavenged):
				card = top(self.scavenged)
				self.wielder.owner.discard(card)
				remove(card, self.scavenged)
				wounding.count = 0
				print('Discarded scavenged card to prevent all damage.')

		#if moving, move held cards.
		elif type(action) is Move and subaction is 3:
			moving = action
			if moving.agent is self.wielder and not isempty(self.scavenged):
				for card in self.scavenged.copy():
					move(card, moving.target, index=moving.target.index(self.wielder))

# +2 atk if another card on same cell.
class StolenWeapons(Ability):
	def __init__(self, wielder):
		super().__init__(wielder, desc="+2 atk if holding a card underneath.")

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if 'scavenged' in self.wielder.__dict__ and len(self.wielder.scavenged) > 0:
			OffsetMod(self.wielder, attname='atk', offset=+2)


# **********************************EVENTS***************************************
class DuckAndCover(Event):
	def __init__(self, owner):
		desc = "Add the Camouflage ability (cannot be attacked by nonadjacent units) to all your sand goblins, for 1 turn."

		super().__init__(owner=owner, desc=desc, faction=SandGoblins)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# add Camouflage ability to unit.
		for unit in self.owner.deck.units:
			#but prevent duplicate ability.
			duplicates = False
			for ability in unit.abilities:
				if isinstance(ability, Camouflage):
					duplicates = True
					break
			if not duplicates:
				ListAddMod(unit.abilities, turns=2, element=Camouflage(wielder=unit))


class Mirage(Event):
	def __init__(self, owner, faction):
		desc = "Move any of your walls on the field to any cell on your side and heal each by up to 3 wounds. Then you may summon things."

		super().__init__(owner=owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		walls = []
		for wall in cardsonboard(type=Wall, owners=[self.owner]):
			add(wall, walls)

		nummoved = 0
		while len(walls) > 0:
			wall = choosefrom(walls, 'Choose a wall.')
			if wall is None:
				if nummoved is 0:
					return False
				else:
					break

			cell = choosefrom(cellsfrom(wall, spaces=0, includeowncell=True) + cellsonboard(team=self.owner.team, onlyempties=True), 'Choose a cell.')
			if cell is None:
				continue

			move(wall, cell)

			# heal the wall up to 3 wounds.
			heals = 0
			while heals < 3 and wall.life < wall.maxlife:
				wall.life += 1
				heals += 1

			nummoved += 1
			remove(wall, walls)

		# let user summon things.
		while len(self.owner.hand) > 0:
			choice = choosefrom(summonablecards(self.owner), msg='Choose a unit to summon.')
			if choice is None:
				break

			cell = choosefrom(choice.getsummoncells(), msg='Choose a cell next to wall.')
			if cell is None:
				continue
			self.owner.summon(choice, cell)



class Shiny(Event):
	def __init__(self, owner, faction):
		desc = "Add Stolen Weapons ability (+2 atk if holding a card underneath) to all your Units with the Scavenge ability, for one turn."
		super().__init__(owner=owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		for unit in cardsonboard(owners=[self.owner], type=Unit):
			for ability in unit.abilities:
				if isinstance(ability, Scavenge):
					ListAddMod(unit.abilities, element=StolenWeapons(wielder=unit), turns=1)
					break


class Taunt(Event):
	def __init__(self, owner):
		desc = "Move up to 2 Common enemies next to a sand goblin of yours up to 3 spaces away from it."
		super().__init__(owner=owner, desc=desc, faction=SandGoblins)

	def use(self, whoseturn, phase, subphase, action, subaction):
		units = []
		for unit in cardsonboard(owners=self.owner.enemyteam, type=Common):  # all onboard units
			if len(cardsfrom(unit, spaces=3, owners=[self.owner], type=Unit)) > 0:  #whose units 3 spaces from them belong to us
				add(unit, units)  #add to list

		nummoved = 0
		while nummoved < 2:
			# choose enemy unit.
			unit = choosefrom(units, msg='Choose an enemy unit.')
			if unit is None:
				if nummoved is 0:
					return False
				else:
					break

			cells = []
			for card in cardsfrom(unit, spaces=3, owners=[self.owner], type=Unit):
				for cell in cellsfrom(card, spaces=1, onlyempties=True):
					add(cell, cells)

			#choose cell.
			cell = choosefrom(cells, msg='Choose a cell.')
			if cell is None:
				continue

			#move it to cell.
			move(unit, cell)

			remove(unit, units)
			nummoved += 1



# **********************************COMMONS***************************************

class Bomber(Common):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=1, range=3, cost=0, maxlife=1, faction=SandGoblins)
		Hasty(wielder=self)

class Javelineer(Common):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=1, range=3, cost=1, maxlife=2, faction=SandGoblins)
		add(Camouflage(self), self.abilities)


class Scavenger(Common):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=1, range=1, cost=1, maxlife=2, faction=SandGoblins)
		Scavenge(wielder=self)

class Shaman(Common):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=1, maxlife=1, faction=SandGoblins)
		Escape(wielder=self)


class Slayer(Common):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=2, maxlife=2, faction=SandGoblins)
		BloodCraze(wielder=self)

# **********************************CHAMPIONS***************************************

class Kreep(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=1, cost=4, maxlife=6, faction=SandGoblins)
		Cowardly(wielder=self)


class Biter(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=1, cost=4, maxlife=6, faction=SandGoblins)
		Crazed(wielder=self)

class SandWyrm(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=4, range=1, cost=6, maxlife=6, faction=SandGoblins)
		Burrow(wielder=self)

class Silts(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=7, maxlife=6, faction=SandGoblins)
		Cunning(wielder=self)

class Stink(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=1, range=3, cost=5, maxlife=3, faction=SandGoblins)
		Lucky(wielder=self)

class Tark(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=5, maxlife=4, faction=SandGoblins)
		Conceal(wielder=self)

# **********************************SUMMONERS***************************************

class Krusk(Summoner):
	def __init__(self):
		setupdict = {(3, 2): Javelineer, (3, 3): Javelineer, (4, 3): Scavenger, (6, 3): Scavenger, (5, 1): Shaman, (5, 3): Wall, (5, 2): Krusk}
		events = [Shiny(self, faction=SandGoblins) for count in range(2)] + [Taunt(self) for count in range(3)] + [DuckAndCover(self) for count in range(3)] + [Mirage(self, faction=SandGoblins)]
		super().__init__(atk=2, range=3, maxlife=6, events=events, setupdict=setupdict, faction=SandGoblins)
		Sandstorm(wielder=self)

# **********************************DECKS***************************************
class DefaultSandGoblinsDeck(Deck):
	def __init__(self):
		summoner = Krusk()
		walls = [Wall(summoner, faction=SandGoblins) for count in range(3)]
		commons = [Shaman(summoner) for count in range(8)] + [Javelineer(summoner) for count in range(2)] + [Scavenger(summoner) for count in range(2)] + [Bomber(summoner) for count in range(6)]
		champions = [Kreep(summoner), Stink(summoner), Biter(summoner)]
		super().__init__(summoner, commons, champions, walls)

class SandGoblins(Faction):
	path = r'decks\sandgoblins\pics'
	commonclasses = [Bomber, Javelineer, Scavenger, Shaman, Slayer]
	championclasses = [Kreep, Biter, SandWyrm, Silts, Stink, Tark]
	summonerclasses = [Krusk]

defaultdeckclasses[SandGoblins] = DefaultSandGoblinsDeck
add(SandGoblins, factions)