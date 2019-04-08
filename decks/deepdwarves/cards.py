from summonerwars.events import *
from summonerwars.abilities import *

# **********************************ABILITIES***************************************

class ChannelMagic(Ability):
	def __init__(self, wielder):
		desc = "When destroyed a card and put into your magic pile, move 1 card from your discard pile to your magic pile."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.agent is self.wielder and action.target in self.wielder.owner.magicpile:
			move(top(self.wielder.owner.discardpile), self.wielder.owner.magicpile)


class GemOfCalling(Ability):
	# cost: 1
	# buy at: movement phase
	# use at: ''
	# effect: choose a common unit up to 4 spaces from wielder and move it next to wielder. Wielder can no longer move.
	def __init__(self, wielder):
		desc = "buy at: movement phase\n\neffect: Move a Common that's up to 4 spaces from wielder next to wielder. Wielder can no longer move."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose card 4 spaces from wielder.
		common = choosefrom(cardsfrom(self.wielder, spaces=4, type=Common), 'Choose a common unit up to 4 spaces away.')
		if common is None:
			return False

		# choose cell next to wielder.
		cell = choosefrom(cellsfrom(self.wielder, spaces=1, onlyempties=True), 'Choose an adjacent cell.')
		if cell is None:
			return False

		# move it there.
		move(common, cell)

		# wielder can no longer move.
		add(self.wielder, self.wielder.owner.moved)
		self.wielder.movesleft = 0



class GemMagic(Ability):
	# cost: 1
	# buy at: attack begin
	# use at: attack begin
	# effect: add 1 to atk til end of turn.
	def __init__(self, wielder):
		desc = "buy at: attack begin\n\neffect: wielder gets +1 atk until end of turn."
		Ability.__init__(self, wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase is 1

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, turns=1, attname='atk', offset=+1)



class GemMagic2(Ability):
	# cost: 1
	# buy at: attack end
	# use at: attack end
	# effect: put wielder next to wall.
	def __init__(self, wielder):
		desc = "buy at: attack end\n\neffect: move next to wall."
		super().__init__(wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase is 3

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose a cell next to wall.
		cell = choosefrom(wallcells(self.wielder.owner), 'Choose a cell next to wall.')
		if cell is None:
			return False

		# move there.
		move(self.wielder, cell)



class Insight(Ability):
	usingsummoners = []
	# cost: 1
	# buy at: any phase
	# use at: any phase
	# effect: a controlled unit attacking an enemy unit that's adjacent to a friendly scholar gets +1 atk during that attack.
	def __init__(self, wielder):
		desc = "buy at: any phase\n\nuse at: attack phase\n\neffect: a controlled unit attacking an enemy unit that's adjacent to a friendly scholar gets +1 atk during that attack."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return len(cardsonboard(type=Scholar, owners=[self.wielder.owner])) >= 1 and self.wielder.owner not in Insight.usingsummoners

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return not self.used and self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		add(self.wielder.owner, Insight.usingsummoners)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if self.used and type(action) is Attack and subaction is 1 and action.agent.owner is self.wielder.owner and len(cardsfrom(action.target, spaces=1, owners=self.wielder.owner.team, type=Scholar)) > 0:
			def render():
				action.agent.atk += 1
				Attack.render(action)
				action.agent.atk -= 1

			action.render = render
			print('Insight ability gave +1 atk.')

	def refresh(self):
		super().refresh()
		remove(self.wielder.owner, Insight.usingsummoners)


class MagePush(Ability):
	# cost: 1
	# buy at: any phase
	# use at: ''
	# effect: move a unit that's up to 2 spaces from wielder up to 2 spaces.
	def __init__(self, wielder):
		desc = "buy at: any phase\n\neffect: move a unit that's up to 2 spaces from wielder up to 2 spaces."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return whoseturn is self.wielder.owner

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)


	def use(self, whoseturn, phase, subphase, action, subaction):
		# get unit.
		unit = choosefrom(cardsfrom(self.wielder, spaces=2, type=Unit))
		if unit is None:
			return False

		# get cell.
		cell = choosefrom(cellsfrom(unit, spaces=2, onlyempties=True))
		if cell is None:
			return False

		# move unit to cell.
		move(unit, cell)



class MagicBlast(Ability):
	def __init__(self, wielder):
		desc = "+2 range."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return canattack(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='range', offset=+2, turns=1)



class Meditate(Ability):
	# cost: 0
	# use at: attack begin, discard pile len > 0
	# effect: move top of discard pile into magic pile. summoner can only let 1 attack this turn.
	def __init__(self, wielder):
		desc = "use at: attack begin\n\neffect: move top of your discard pile into your magic pile. Only 1 Unit can attack this turn."
		super().__init__(wielder=wielder, desc=desc)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase is 1 and len(self.wielder.owner.discardpile) > 0 and len(self.wielder.owner.attacked) < 2

	def use(self, whoseturn, phase, subphase, action, subaction):
		move(top(self.wielder.owner.discardpile), self.wielder.owner.magicpile)
		Mod(self.wielder.owner, attname='allowedattackers', value=1, turns=1)
		print('Moved 1 discarded card to magic pile.')



class Rally(Ability):
	def __init__(self, wielder):
		desc = "+1 atk for this turn if played at least 1 event card this turn. "
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if phase is eventphase and subphase is 2: #TODO: should include 'instant' events
			OffsetMod(self.wielder, attname='atk', offset=+1, turns=1)
			return True


class Restructure(Ability):
	# cost: 1
	# buy at: turn end
	# use at: ''
	# effect: move a wall being adjacent to wielder, to cell on your side 2 spaces from wielder.
	def __init__(self, wielder):
		desc = "buy at: turn end\n\neffect: move an adjacent wall to a cell on your side up to 2 spaces from wielder."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is magicphase and subphase is 3 and len(cardsfrom(self.wielder, spaces=1, type=Wall)) > 0

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose wall.
		wall = choosefrom(cardsfrom(self.wielder, spaces=1, type=Wall), msg='Choose a wall.')
		if wall is None:
			return False

		# choose cell.
		cell = choosefrom(cellsfrom(self.wielder, spaces=2, onlyempties=True), msg='Choose a cell.')
		if cell is None:
			return False

		# move wall to cell.
		move(wall, cell)



class RockEater(Ability):
	def __init__(self, wielder):
		desc = "+1 atk when attacking a wall. If wounded a wall in an attack, heal wielder by 1."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and isinstance(action.target, Wall):
			def render():
				action.agent.atk += 1
				Attack.render(action)
				action.agent.atk -= 1

			action.render = render
			print('Rock Eater ability gave +1 atk.')
		if type(action) is Attack and subaction is 3 and isinstance(action.target, Wall) and action.numwounds > 0:
			self.wielder.life += 1


class ShardOfTheFatherGem(Ability):
	def __init__(self, wielder):
		desc = "Put any destroyed Unit within 2 spaces of wielder into your magic pile (instead of any others')."
		super().__init__(wielder=wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.startcell in cellsfrom(self.wielder, spaces=2):
			move(action.target, self.wielder.owner.magicpile)


class Tunnel(Ability):
	# cost: 1
	# buy at: move begin
	# use at: move
	# effect: move miner next to another miner instead of normal movement.
	def __init__(self, wielder):
		desc = "buy at: move begin\n\nuse at: move phase\n\neffect: move next to a miner instead of normal movement."
		super().__init__(wielder=wielder, cost=1, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase and subphase is 1

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is movephase and canmove(self.wielder)

	def use(self, whoseturn, phase, subphase, action, subaction):
		cells = []
		# get own miners on board.
		for miner in cardsonboard(owners=[self.wielder.owner], type=Miner):
			if miner is self.wielder:
				continue
			# add their adjacent squares to list.
			cells += cellsfrom(miner, spaces=1, onlyempties=True)  # choose from list to tunnel to.

		# choose one of those cells.
		cell = choosefrom(cells, 'Choose a cell next to a miner.')
		if cell is None:
			return False

		# move there.
		move(self.wielder, cell)
		self.wielder.movesleft = 0
		add(self.wielder, self.wielder.owner.moved)


# **********************************EVENTS***************************************
class IllusionaryWarrior(Event):
	def __init__(self, owner):
		desc = "Move a Common from your magic pile adjacent to a controlled deep dwarf Champion or Gem Mage. You control it."
		super().__init__(owner, desc=desc, faction=DeepDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose common unit.
		unit = choosefrom([unit for unit in self.owner.magicpile if isinstance(unit, Common)], msg='Choose a unit from magic pile.')
		if unit is None:
			return False

		# choose cell next to a champion or gem mage.
		lst = []
		for card in self.owner.deck.units:
			if onboard(card) and (isinstance(card, GemMage) or isinstance(card, Champion)):
				for cell in cellsfrom(card, spaces=1, onlyempties=True):
					add(cell, lst)
		cell = choosefrom(lst, msg='Choose a cell next to a Champion or Gem Mage.')
		if cell is None:
			return False

		# move unit there.
		unit.owner = self.owner
		unit.life = unit.maxlife
		move(unit, cell)


class MagicStasis(Event):
	def __init__(self, owner):
		desc = "Choose an opponent to not be able to magic points during his next turn."
		super().__init__(owner, desc=desc, faction=DeepDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# choose summoner.
		summoner = choosefrom(self.owner.enemyteam, msg='Choose an enemy summoner.')
		if summoner is None:
			return False

		# apply modifier.
		for card in summoner.deck:
			if 'cost' in card.__dict__:
				if card.cost > 0:
					Mod(card, attname='cost', value=999, turns=2)
			if isinstance(card, Unit):
				for ability in card.abilities:
					if ability.cost > 0:
						Mod(ability, attname='cost', value=999, turns=2)


class MagicTorrent(Event):
	def __init__(self, owner):
		desc = "Spend 1 magic per enemy Common or Champion up to 4 spaces from your Summoner and wound each by 1."
		super().__init__(owner, desc=desc, faction=DeepDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		wounded = []
		while not isempty(self.owner.magicpile):
			# choose and wound enemy common or champion 4 spaces from summoner.
			choice = choosefrom([card for card in cardsfrom(self.owner, spaces=4, owners=self.owner.enemyteam) if isinstance(card, Common) or isinstance(card, Champion) and card not in wounded], msg='Choose a unit to wound.')
			if choice is None:
				return not isempty(wounded)

			#pay.
			move(top(self.owner.magicpile), self.owner.discardpile)

			#wound.
			self.owner.wound(choice)

			#add to already wounded.
			add(choice, wounded)


class WakeTheFatherGem(Event):
	def __init__(self, owner):
		desc = "All your units' abilities cost 1 less magic."
		super().__init__(owner, desc=desc, faction=DeepDwarves)

	def use(self, whoseturn, phase, subphase, action, subaction):
		for unit in self.owner.deck.units:
			for ability in unit.abilities:
				if ability.cost > 0:
					OffsetMod(ability, turns=1, attname='cost', offset=-1)



# **********************************COMMONS***************************************
class BattleMage(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=2, maxlife=2, faction=DeepDwarves)
		MagicBlast(wielder=self)


class Crossbowman(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=1, maxlife=1, faction=DeepDwarves)
		Rally(wielder=self)


class GemMage(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=3, cost=2, maxlife=1, faction=DeepDwarves)
		GemMagic(wielder=self)
		GemMagic2(wielder=self)


class Miner(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=DeepDwarves)
		Tunnel(wielder=self)


class Scholar(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=0, range=1, cost=1, maxlife=3, faction=DeepDwarves)
		Insight(wielder=self)


# **********************************CHAMPIONS***************************************

class DeepTroll(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=7, maxlife=7, faction=DeepDwarves)
		RockEater(wielder=self)


class Gren(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=5, maxlife=4, faction=DeepDwarves)
		ShardOfTheFatherGem(wielder=self)


class Kynder(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=5, maxlife=6, faction=DeepDwarves)
		MagePush(wielder=self)


class Piclo(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=1, cost=7, maxlife=5, faction=DeepDwarves)
		ChannelMagic(wielder=self)


class Sprog(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=6, maxlife=6, faction=DeepDwarves)
		Restructure(wielder=self)


class Lun(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=1, cost=4, maxlife=4, faction=DeepDwarves)
		GemOfCalling(wielder=self)


# **********************************SUMMONERS***************************************
class Tundle(Summoner):
	def __init__(self):
		setupdict = {(1, 2): Miner, (2, 4): Miner, (6, 4): Miner, (2, 3): Scholar, (3, 2): GemMage, (3, 3): Wall, (2, 2): Tundle}
		events = [IllusionaryWarrior(self) for count in range(2)] + [SummoningSurge(self, faction=DeepDwarves) for count in range(2)] + [MagicStasis(self) for count in range(2)] + [WakeTheFatherGem(self) for count in range(2)] + [MagicTorrent(self) for count in range(1)]
		super().__init__(atk=2, range=3, maxlife=6, events=events, setupdict=setupdict, faction=DeepDwarves)
		Meditate(wielder=self)


# **********************************FACTION***************************************
class DefaultDeepDwarvesDeck(Deck):
	def __init__(self):
		summoner = Tundle()
		commons = [Scholar(summoner) for count in range(5)] + [Miner(summoner) for count in range(7)] + [GemMage(summoner) for count in range(6)]
		champions = [Sprog(summoner), Kynder(summoner), Lun(summoner)]
		walls = [Wall(summoner, faction=DeepDwarves) for count in range(3)]
		super().__init__(summoner=summoner, commons=commons, champions=champions, walls=walls)


class DeepDwarves(Faction):
	path = r'decks\deepdwarves\pics'
	commonclasses = [BattleMage, Crossbowman, GemMage, Miner, Scholar]
	championclasses = [DeepTroll, Gren, Kynder, Piclo, Sprog, Lun]
	summonerclasses = [Tundle]

defaultdeckclasses[DeepDwarves] = DefaultDeepDwarvesDeck
add(DeepDwarves, factions)