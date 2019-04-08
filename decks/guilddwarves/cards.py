from summonerwars.events import *
from summonerwars.abilities import *

# **********************************ABILITIES***************************************
class Bravery(Ability):
	def __init__(self, wielder):
		desc = "+1 atk against a unit with > 1 summon cost."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and action.target.cost > 1:
			def render():
				action.agent.atk += 1
				Attack.render(action)
				action.agent.atk -= 1
			action.render = render
			print('Bravery ability gave +1 atk.')

class Built(Ability):
	def __init__(self, wielder):
		desc = "Cannot move. Can be summoned next to a controlled Architect."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		Mod(self.wielder, attname='movesleft', value=0)
		if type(action) is GetSummonCells and subaction is 2 and action.agent is self.wielder:
			for card in cardsonboard(owners=[self.wielder.owner], type=Architect):
				action.lst += cellsfrom(card, spaces=1, onlyempties=True)

class Charge(Ability):
	def __init__(self, wielder):
		desc = "+2 moves during move phase, but cannot attack for the turn if used any of these extra meves."
		super().__init__(wielder=wielder, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner:
			if phase is movephase:
				OffsetMod(self.wielder, attname='movesleft', offset=+2)
				if type(action) is Move and subaction is 2:
					if self.wielder.movesleft - action.count < DEFAULT_MOVES:
						self.activated = True
			if self.activated:
				Mod(self.wielder, attname='attacksleft', value=0)

	def refresh(self):
		super().refresh()
		self.activated = False

class Engage(Ability):
	def __init__(self, wielder):
		desc = 'Cannot move when adjacent to an enemy Unit.'
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if len(cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam, type=Unit)) > 0:
			Mod(self.wielder, attname='movesleft', value=0)


class ExplosiveShell(Ability):
	def __init__(self, wielder):
		desc = "Can attack any card 3 cells away. Destroying any card wounds any cards adjacent to it by 1."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#increase targets.
		if type(action) is GetTargetCards and subaction is 2 and action.agent is self.wielder:
			action.lst = cardsfrom(self.wielder, spaces=3)

		#wound all adjacent cards if killed something.
		if type(action) is Attack and subaction is 3 and action.agent is self.wielder and action.target.life <= 0:
			for card in cardsfrom(action.startcell, spaces=1):
				self.wielder.wound(card)


class GreaterStoneMelding(Ability):
	def __init__(self, wielder):
		desc = "If wielder is next to a wall, that wall and all friendly units adjacent to that wall only receive wounds from enemy rolls of > 3."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent.owner in self.wielder.owner.enemyteam:
			for wall in cardsfrom(self.wielder, spaces=1, type=Wall):
				if action.target is wall or (action.target.owner in self.wielder.owner.team and isadjacent(action.target, wall)):
					action.rolltohit = 4
					break

class GyroStabilizer(Ability):
	def __init__(self, wielder):
		desc = "Can attack 2 clear diagonal line spaces away. Spend 1 magic point to attack again."
		super().__init__(wielder=wielder, cost=1, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#diagonal ranged attack.
		if type(action) is GetTargetCards and subaction is 2 and action.agent is self.wielder:
			action.lst += diagonalcardsfrom(self.wielder, spaces=2, blockedlos=True)

		#prompt to attack again.
		if not self.activated and type(action) is Attack and subaction is 3 and action.agent is self.wielder:
			if self.cost <= 0 or len(self.wielder.owner.magicpile) >= self.cost and choosefrom([True, False], msg='Want to be able to attack again (cost: 1)?') is True:
				for cost in range(self.cost):
					self.wielder.owner.discard(top(self.wielder.owner.magicpile))
				self.wielder.attacksleft += 1
				self.activated = True

	def refresh(self):
		super().refresh()
		self.activated = False


class HammerQuake(Ability):
	def __init__(self, wielder):
		desc = "Affect all cards within 2 cells but self when attacking."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 2 and action.agent is self.wielder:
			#make attacks on every card 2 spaces away, using one same roll list.
			for card in cardsfrom(self.wielder, spaces=2):
				if card is not action.target:
					attack = Attack(self.wielder, card)
					def render():
						attack.rolllist = action.rolllist #set to old roll list
						attack.numhits = len([roll for roll in attack.rolllist if roll >= attack.rolltohit])

					attack.render = render
					execute(attack)

class MagicBarrier(Ability):
	def __init__(self, wielder):
		desc = "Prevent all wounds from an attack. Can use only once per turn."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 2:
			if action.numhits > 0:
				if len(self.wielder.owner.magicpile) >= self.cost and choosefrom([True, False], msg='Spend 1 magic to prevent all wounds?') is True:
					for cost in range(self.cost):
						self.wielder.owner.discard(top(self.wielder.owner.magicpile))
					action.numhits = 0
					return True

class MightyLegs(Ability):
	def __init__(self, wielder):
		desc = "Can move even if has Built. Can only attack adjacent cards for the turn if moved. Can move through common units. Can move through Commons, and wounds it if does."
		super().__init__(wielder=wielder, desc=desc)
		self.cellsmoved = 0

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase and self.wielder.movesleft >= 2 and (len(self.wielder.owner.moved) < self.wielder.owner.allowedmovers or self.wielder in self.wielder.owner.moved) and not isempty(cardsfrom(self.wielder, spaces=1, type=Common))

	#trample.
	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose an adjacent cell with Common on it.
		cell = choosefrom([cell for cell in cellsfrom(self.wielder, spaces=1, onlyempties=False) if len(cardsfrom(cell, spaces=0, type=Common)) > 0], msg='Choose an adjacent cell with a Common on it.')
		if cell is None:
			return False

		#move there and wound the trampled.
		self.wielder.move(cell)
		for trampled in cardsfrom(self.wielder, spaces=0, type=Common):
			self.wielder.wound(trampled)

		#choose an adjacent empty cell.
		while True:
			cell = choosefrom(cellsfrom(self.wielder, spaces=1, onlyempties=True), msg='Choose an adjacent empty cell.')
			if cell is not None:
				break

		#move there.
		self.wielder.move(cell)

	#Can move. Can only attack adjacent cards for the turn if moved
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#let wielder move if it can't.
		for ability in self.wielder.abilities:
			if isinstance(ability, Built):
				self.wielder.movesleft = DEFAULT_MOVES - self.cellsmoved
				break

		#remember if moved.
		if type(action) is Move and subaction is 2 and action.agent is self.wielder:
			if action.count > 0:
				self.cellsmoved += action.count

		#disallow attacking nonadjacent units if moved.
		if self.cellsmoved > 0 and type(action) is GetTargetCards and subaction is 2 and action.agent is self.wielder:
			for card in action.lst.copy():
				if not isadjacent(card, self.wielder):
					remove(card, action.lst)

	def refresh(self):
		super().refresh()
		self.cellsmoved = 0

class Rage(Ability):
	def __init__(self, wielder):
		desc = "Before an attack from wielder, can wound self up to 2 wounds to add that much atk for the rest of turn."
		super().__init__(wielder=wielder, desc=desc)
		self.activated = False

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return not self.activated

	def use(self, whoseturn, phase, subphase, action, subaction):
		numwounds = choosefrom([1, 2], msg='Choose number of wounds to apply to self.')
		OffsetMod(self.wielder, attname='atk', offset=+numwounds, turns=1)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#disable ability if attacked.
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder:
			self.activated = True

	def refresh(self):
		self.activated = False

class Repair(Ability):
	def __init__(self, wielder):
		desc = "Heal an adjacent Built unit instead of attacking."
		super().__init__(wielder=wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return (phase is attackphase and subphase < 3) and canattack(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# get walls and units.
		walls = [wall for wall in cardsfrom(self.wielder, spaces=1, type=Wall)]
		units = [unit for unit in cardsfrom(self.wielder, spaces=1, type=Unit) if unit.life < unit.maxlife for ability in unit.abilities if isinstance(ability, Built)]

		#choose a unit.
		choice = choosefrom(units + walls, msg='Choose a wall or unit with Built to heal.')
		if choice is None:
			return False

		#heal it.
		execute(Heal(self.wielder, choice, numheals=1))

		#decrement attacks left.
		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)



class RuneOfProtection(Ability):
	def __init__(self, wielder):
		desc = "Force enemy attackers of controlled commons adjacent to wielder to roll > 4 to hit."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent.owner in self.wielder.owner.enemyteam:
			if action.target.owner is self.wielder.owner and isinstance(action.target, Common) and isadjacent(action.target, self.wielder):
				action.rolltohit = 5
				print(name(self.wielder) + "'s rune of protection protected.")

class SiegeEngine(Ability):
	def __init__(self, wielder):
		desc = "5 range. Cannot attack if moved. +2 atk when targeting walls."
		super().__init__(wielder=wielder, desc=desc)
		self.activated = False

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		#increase range.
		Mod(self.wielder, attname='range', value=5)

		#increase atk against walls.
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and isinstance(action.target, Wall):
			def render():
				action.agent.atk += 2
				Attack.render(action)
				action.agent.atk -= 2
			action.render = render
			print('SiegeEngine ability gave +2 atk.')

		#cannot attack if moved.
		if type(action) is Move and subaction is 2 and action.agent is self.wielder and action.count > 0:
			self.activated = True
		if self.activated:
			self.wielder.attacksleft = 0

	def refresh(self):
		super().refresh()
		self.activated = False


class ShieldBlock(Ability):
	def __init__(self, wielder):
		desc = "Enemies attacking wielder must roll hits on all dice to wound."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 2 and action.agent.owner in self.wielder.owner.enemyteam and action.target is self.wielder:
			for roll in action.rolllist:
				if roll < DEFAULT_HIT_VALUE:
					action.numhits = 0

class StoneMelding(Ability):
	def __init__(self, wielder):
		desc = "If next to a wall, Forces opponent attackers of wielder to roll > 3 to wound."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if not isempty(cardsfrom(self.wielder, spaces=1, type=Wall)):
			if type(action) is Attack and subaction is 1 and action.target is self.wielder and action.agent.owner in self.wielder.owner.enemyteam:
				def render():
					action.rolltohit = 4
				action.render = render


class StrengthOfTheStone(Ability):
	def __init__(self, wielder):
		desc = "Wound all your walls before attacking to + that many walls to your atk for that attack."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder:
			if choosefrom([True, False], 'Wound all your walls to add that much to attack?') is True:
				count = 0
				for wall in cardsonboard(owners=[self.wielder.owner], type=Wall):
					self.wielder.wound(wall)
					count += 1

				def render():
					action.agent.atk += count
					Attack.render(action)
					action.agent.atk -= count
				action.render = render

class StructuralAnalysis(Ability):
	def __init__(self, wielder):
		desc = "+2 atk when attacking Walls."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and isinstance(action.target, Wall):
			def render():
				action.agent.atk += 2
				Attack.render(action)
				action.agent.atk -= 2

			action.render = render

class Thrust(Ability):
	def __init__(self, wielder):
		desc = "+1 atk when attacking adjacent cards."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.agent is self.wielder and isadjacent(self.wielder, action.target):
			def render():
				action.agent.atk += 1
				Attack.render(action)
				action.agent.atk -= 1

			action.render = render
			print("Thrust ability gave +1 atk.")


class Tough(Ability):
	def __init__(self, wielder):
		desc = "rolls only attack wielder rolled when > 3."
		super().__init__(wielder=wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.target is self.wielder and action.agent.owner in self.wielder.owner.enemyteam:
			def render():
				action.rolltohit = 4
			action.render = render


# **********************************EVENTS***************************************
class AcceleratedConstruction(Event):
	def __init__(self, owner):
		desc = "Search any card in the draw pile with Built ability. Place in your hand and shuffle drawpile. Can summon units with Built."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		#get a Built from drawpile and shuffle it.
		choice = choosefrom([card for card in self.owner.drawpile if isinstance(card, Unit) for ability in card.abilities if isinstance(ability, Built)], 'choose a card from your drawpile with Built.')
		if choice is None:
			return False
		move(choice, self.owner.hand)
		shuffle(self.owner.drawpile)

		#summon built units.
		while not isempty(self.owner.hand):
			choice = choosefrom(summonablecards(self.owner, ability=Built), msg='Choose a unit with Built to summon.')
			if choice is None:
				break

			#add cells next to built units.
			cell = choosefrom(choice.getsummoncells() + cardsonboard(ability=Built), msg='Choose a cell next to wall.')
			if cell is None:
				continue
			self.owner.summon(choice, cell)

class Besiege(Event):
	def __init__(self, owner):
		desc = "Wound by 3 each of an opponent's walls."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		summoner = choosefrom(self.owner.enemyteam, 'choose an opponent.')
		if summoner is None:
			return False

		for wall in summoner.deck.walls:
			if onboard(wall):
				self.owner.wound(wall, 3)


class Destabilize(Event):
	def __init__(self, owner):
		desc = "Wound every wall by 4."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		for wall in cardsonboard(type=Wall):
			self.owner.wound(wall, 4)

class Expand(Event):
	def __init__(self, owner):
		desc = "Summon a Common with Built from your hand for free."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom(summonablecards(self.owner, type=Common, ability=Built, free=True), msg='Choose a common with Built to summon.')
		if choice is None:
			return False

		cell = choosefrom(choice.getsummoncells(), msg='Choose a cell next to wall.')
		if cell is None:
			return False

		self.owner.summon(choice, cell, free=True)


class HeroicFeat(Event):
	def __init__(self, owner):
		desc = "+2 atk to any Unit for 1 turn."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		choice = choosefrom([card for card in cardsonboard(type=Unit)], msg='Choose a unit.')
		if choice is None:
			return False

		OffsetMod(choice, attname='atk', offset=+2, turns=1)


class Reinforcements(Event):
	def __init__(self, owner):
		desc = "Summon up to 2 commons for free if you have less units on board than any opponent."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# cannot proceed if no opponent has less units than you.
		ok = False
		for opponent in self.owner.enemyteam:
			if len(cardsonboard(owners=[opponent], type=Unit)) > len(cardsonboard(owners=[self.owner], type=Unit)):
				ok = True
				break
		if not ok:
			return False

		# freely summon up to 2 commons.
		summoned = 0
		while summoned < 2:
			choice = choosefrom(summonablecards(self.owner, type=Common), msg='Choose a common to summon.')
			if choice is None:
				return summoned > 0

			cell = choosefrom(choice.getsummoncells(), 'choose a cell to summon onto.')
			if cell is None:
				continue

			self.owner.summon(choice, cell, free=True)
			summoned += 1

class StrengthenSturcturesMod(GameMod):
	def use(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.target.owner is self.owner:
			rightcard = False
			if isinstance(action.target, Unit):
				for ability in action.target.abilities:
					if isinstance(ability, Built):
						rightcard = True
			if isinstance(action.target, Wall):
				rightcard = True
			if rightcard:
				action.rolltohit = 5
				print('Strengthen Structures Event requires roll of 5 to hit.')

class StrengthenStructures(Event):
	def __init__(self, owner):
		desc = "Force all enemy units to need to roll > 4 to wound a controlled wall or unit with Built."
		super().__init__(owner, desc=desc, faction=GuildDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		StrengthenSturcturesMod(self.owner, turns=2)


# **********************************upgrades***************************************
class UpgradeMod(GameMod):
	def __init__(self, upgrader, upgraded, abilityclass):
		super().__init__(owner=upgrader.owner)
		self.upgrader = upgrader
		self.upgraded = upgraded
		self.abilityclass = abilityclass
		self.ability = abilityclass(wielder=self.upgraded)

	def use(self, whoseturn, phase, subphase, action, subaction):
		#move with upgraded card.
		if type(action) is Move and subaction is 3 and action.agent is self.upgraded:
			moveunder(self.upgrader, self.upgraded)

		#put in magic pile if upgraded is killed.
		if type(action) is Wound and subaction is 3 and action.target is self.upgraded and action.target.life <= 0:
			move(self.upgrader, action.agent.owner.magicpile)
			remove(self.ability, self.upgraded.abilities)
			remove(self, gamemods)

class Upgrade(Event):
	def __init__(self, owner, abilityclass):
		desc = "Choose a unit to put this card under it. Add Mighty Legs ability to chosen unit while under it."
		super().__init__(owner=owner, desc=desc, faction=GuildDwarves, discardonuse=False)
		self.choice = None
		self.abilityclass = abilityclass

	def use(self, whoseturn, phase, subphase, action, subaction):
		#choose a unit to upgrade.
		self.choice = choosefrom([unit for unit in self.owner.deck.units for ability in unit.abilities if isinstance(ability, Built)], 'choose a unit with Built to upgrade.')
		if self.choice is None:
			return False

		#move card under it.
		moveunder(self, self.choice)

		#add a game mod.
		UpgradeMod(self, self.choice, self.abilityclass)


class ColossusUpgrade(Upgrade):
	def __init__(self, owner):
		super().__init__(owner, MightyLegs)

class MortarUpgrade(Upgrade):
	def __init__(self, owner):
		super().__init__(owner, ExplosiveShell)

class TurretUpgrade(Upgrade):
	def __init__(self, owner):
		super().__init__(owner, GyroStabilizer)

# **********************************COMMONS***************************************
class Architect(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=0, maxlife=1, faction=GuildDwarves)
		Repair(wielder=self)

class AssaultTower(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=2, maxlife=3, faction=GuildDwarves)
		Built(wielder=self)

class Ballista(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=2, maxlife=3, faction=GuildDwarves)
		SiegeEngine(wielder=self)

class Defender(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=GuildDwarves)
		Engage(wielder=self)

class Engineer(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=1, faction=GuildDwarves)
		StructuralAnalysis(wielder=self)

class Guardsman(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=3, faction=GuildDwarves)
		Tough(wielder=self)

class OathSworn(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=GuildDwarves)
		Bravery(wielder=self)

class Spearman(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=1, maxlife=1, faction=GuildDwarves)
		Thrust(wielder=self)

# **********************************CHAMPIONS***************************************
class Baldar(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=1, cost=4, maxlife=4, faction=GuildDwarves)
		ShieldBlock(wielder=self)

class Dwaf(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=5, maxlife=5, faction=GuildDwarves)
		StructuralAnalysis(wielder=self)

class Gror(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=7, maxlife=7, faction=GuildDwarves)
		HammerQuake(wielder=self)


class Grundor(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=4, range=1, cost=6, maxlife=5, faction=GuildDwarves)
		Charge(wielder=self)

class GrundorsTower(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=6, maxlife=8, faction=GuildDwarves)
		Built(wielder=self)

class Halvor(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=1, range=1, cost=5, maxlife=8, faction=GuildDwarves)
		Rage(wielder=self)

class Thorkur(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=3, cost=6, maxlife=4, faction=GuildDwarves)
		MagicBarrier(wielder=self)

class Tordok(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=5, maxlife=4, faction=GuildDwarves)
		RuneOfProtection(wielder=self)


class Ulfric(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=6, maxlife=6, faction=GuildDwarves)
		GreaterStoneMelding(wielder=self)

# **********************************SUMMONERS***************************************
class Bolvi(Summoner):
	def __init__(self):
		setupdict = {(2, 4) : OathSworn, (2, 3) : AssaultTower, (2, 2) : Bolvi, (3, 3): OathSworn, (3, 2) : Architect, (4, 2) : Wall, (5, 3) : OathSworn}
		events = [Expand(self) for count in range(2)] + [StrengthenStructures(self) for count in range(2)] + [AcceleratedConstruction(self) for count in range(1)] + [Destabilize(self) for count in range(1)] + [MortarUpgrade(self) for count in range(1)] + [TurretUpgrade(self) for count in range(1)] + [ColossusUpgrade(self) for count in range(1)]
		super().__init__(atk=2, range=3, maxlife=6, events=events, setupdict=setupdict, faction=GuildDwarves)
		StrengthOfTheStone(wielder=self)

class Oldin(Summoner):
	def __init__(self):
		setupdict = {(1, 2) : Spearman, (2, 4) : Defender, (3, 2) : Engineer, (4, 1) : Oldin, (4, 3) : Wall, (5, 3) : Defender, (6, 2) : Spearman}
		events = [HeroicFeat(self) for count in range(2)] + [Besiege(self) for count in range(2)] + [MagicDrain(self, faction=GuildDwarves) for count in range(2)] + [Reinforcements(self) for count in range(2)] + [AHeroIsBorn(self, faction=GuildDwarves) for count in range(1)]
		super().__init__(atk=2, range=3, maxlife=6, events=events, setupdict=setupdict, faction=GuildDwarves)
		StoneMelding(wielder=self)

# **********************************FACTION***************************************
class DefaultDeepDwarvesDeck(Deck):
	def __init__(self):
		summoner = Bolvi()
		commons = [OathSworn(summoner) for count in range(3)] + [Architect(summoner) for count in range(9)] + [AssaultTower(summoner) for count in range(6)]
		champions = [GrundorsTower(summoner), Gror(summoner), Tordok(summoner)]
		walls = [Wall(summoner, faction=GuildDwarves) for count in range(3)]
		super().__init__(summoner=summoner, commons=commons, champions=champions, walls=walls)


class GuildDwarves(Faction):
	path = r'decks\guilddwarves\pics'
	commonclasses = [Architect, AssaultTower, Ballista, Defender, Engineer, Guardsman, OathSworn, Spearman]
	championclasses = [Baldar, Dwaf, Gror, GrundorsTower, Grundor, Halvor, Thorkur, Tordok, Ulfric]
	summonerclasses = [Bolvi, Oldin]

defaultdeckclasses[GuildDwarves] = DefaultDeepDwarvesDeck
add(GuildDwarves, factions)