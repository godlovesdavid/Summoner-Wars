from math import floor
from summonerwars.abilities import Flight, Rider, GreaterFlight
from summonerwars.events import SummoningSurge, AHeroIsBorn
from summonerwars.menus import *

# **********************************ABILITIES***************************************

class ArrowOfLight(Ability):
	def __init__(self, wielder):
		desc = "If killed a target, make its owner discard a card from his hand."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.target.life <= 0 and action.agent is self.wielder and not isempty(action.target.owner.hand):
			setwhoseturn(action.target.owner)
			while not isempty(action.target.owner.hand):
				card = choosefrom(action.target.owner.hand, name(action.target.owner) + ', choose a card from your hand to discard.')
				if card is None:
					continue
				move(card, action.target.owner.discardpile)
				break
			setwhoseturn(self.wielder.owner)


class HailOfArrows(Ability):
	def __init__(self, wielder):
		desc = "+1 atk per Stalwart Archer adjacent to wielder."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if not isempty(cardsfrom(self.wielder, spaces=1, type=StalwartArcher, owners=[self.wielder.owner])):
			OffsetMod(self.wielder, attname='atk', offset=len(cardsfrom(self.wielder, spaces=1, type=StalwartArcher, owners=[self.wielder.owner])))

class BladeOfLight(Ability):
	def __init__(self, wielder):
		desc = "+1 atk per 2 cards in your magic pile, to a max of +4."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		atkplus = floor(len(self.wielder.owner.magicpile) / 2)
		if atkplus > 4:
			atkplus = 4

		OffsetMod(self.wielder, attname='atk', offset=+atkplus)

class Escort(Ability):
	def __init__(self, wielder):
		desc = "If adjacent to a controlled Common or Champion, if that Common or Champion moves, wielder can be placed next to it after the move."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Move and subaction is 3 and (isinstance(action.agent, Champion) or isinstance(action.agent, Summoner)) and action.agent.owner is self.wielder.owner and isadjacent(self.wielder, action.startcell):
			cell = choosefrom(cellsfrom(action.target, spaces=1, onlyempties=True), msg=name(self.wielder) + str(self.wielder.pos) + ' can escort ' + name(action.agent))
			if cell is None:
				return False

			move(self.wielder, cell)

class GreaterHealing(Ability):
	def __init__(self, wielder):
		desc = "Heal an adjacent Common or Champion by 2 wounds instead of attacking."
		super().__init__(wielder, desc=desc, cost=1)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return (phase is attackphase and subphase < 3) and canattack(self.wielder)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# get commons and champions (if has magic) on board.
		commons = []
		champions = []
		for card in cardsfrom(self.wielder, spaces=1):
			if card.life < card.maxlife:
				if isinstance(card, Common):
					add(card, commons)
				elif isinstance(card, Champion):
					add(card, champions)

		#choose a unit.
		choice = choosefrom(commons + champions, msg='Choose a Common or Champion to heal.')
		if choice is None:
			return False

		#heal it.
		execute(Heal(self.wielder, choice, numheals=2))

		#count it as an attack.
		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)


#todo: need to work with deep dwarves' MagicStasis
class Healing(Ability):
	def __init__(self, wielder):
		desc = "Heal a Common or Champion next to wielder by 1 instead of attacking, but healing a Champion costs 1."
		super().__init__(wielder, desc=desc)

	def isbuyenabled(self, whoseturn, phase, subphase, action, subaction):
		return (phase is attackphase and subphase < 3) and canattack(self.wielder)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return self.isbuyenabled(whoseturn, phase, subphase, action, subaction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		# get commons and champions (if has magic) on board.
		commons = []
		champions = []
		for card in cardsfrom(self.wielder, spaces=1):
			if card.life < card.maxlife:
				if isinstance(card, Common):
					add(card, commons)
				elif isinstance(card, Champion) and len(self.wielder.owner.magicpile) >= 1:
					add(card, champions)

		#choose a unit.
		choice = choosefrom(commons + champions, msg='Choose a Common or Champion to heal.')
		if choice is None:
			return False

		#heal it (if champion, use 1 magic).
		if choice in champions:
			for cost in range(1):
				self.wielder.owner.discard(top(self.wielder.owner.magicpile))
		execute(Heal(self.wielder, choice, numheals=1))

		#decrement attacks left.
		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)



class HeavensRain(Ability):
	def __init__(self, wielder):
		desc = "Roll a die instead of attacking. All enemies within 2 spaces of wielder get wounded by 1 on a roll > 2."
		super().__init__(wielder, desc=desc)
	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return phase is attackphase and subphase < 3 and canattack(self.wielder)
	def use(self, whoseturn, phase, subphase, action, subaction):
		#wound all enemies within 2 spaces on a roll of > 2.
		if self.wielder.roll(1)[0] > 2:
			for enemyunit in cardsfrom(self.wielder, spaces=2, type=Unit, owners=self.wielder.owner.enemyteam, onlyattackables=True):
				self.wielder.wound(enemyunit)

		#decrement attacks left.
		self.wielder.attacksleft -= 1
		add(self.wielder, self.wielder.owner.attacked)




class MysticArts(Ability):
	def __init__(self, wielder):
		desc = "All controlled Woeful Brothers within 4 spaces from wielder get 3 range."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		for card in cardsfrom(self.wielder, spaces=4, type=WoefulBrother, owners=[self.wielder.owner]):
			OffsetMod(card, attname='range', offset=+2)

class Protector(Ability):
	def __init__(self, wielder):
		desc = "Forces enemy units adjacent to wielder to include wielder in their targets when attacking."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is GetTargetCards and subaction is 3 and isinstance(action.agent, Unit) and action.agent.owner in self.wielder.owner.enemyteam and isadjacent(action.agent, self.wielder):
			for card in action.lst.copy():
				protects = False
				if isinstance(card, Unit):
					for ability in card.abilities:
						if isinstance(ability, Protector) or isinstance(ability, ValiantDefender):
							protects = True
				if not protects:
					remove(card, action.lst)

class ShieldOfLight(Ability):
	def __init__(self, wielder):
		desc = "Attackers of controlled Commons within 2 spaces of wielder must roll > 3 to wound them."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1 and action.target in cardsfrom(self.wielder, spaces=2, type=Common, owners=[self.wielder.owner]):
			action.rolltohit = 4

class SwiftManuever(Ability):
	def __init__(self, wielder):
		desc = "Can exchange places with an adjacent Unit if was attacked and received no wounds."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 3 and action.numwounds is 0 and action.target is self.wielder:
			setwhoseturn(self.wielder.owner)
			unit = choosefrom(cardsfrom(self.wielder, spaces=1, type=Unit), msg=name(self.wielder.owner) + ', choose an adjacent card for ' + name(self.wielder) + ' to exchange places with.')
			if unit is None:
				setwhoseturn(whoseturn)
				return False

			switchplaces(self.wielder, unit)
			setwhoseturn(whoseturn)

class SybilsSpirit(Ability):
	def __init__(self, wielder):
		desc = "Attackers of controlled Commons within 2 spaces of wielder must roll > 3 to wound them."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if type(action) is Attack and subaction is 1:
			attack = action
			attack.rolltohit = 4
		elif type(action) is Heal and subaction is 2:
			heal = action
			for count in heal.numheals:
				roll = self.wielder.roll(1)
				if roll[0] < 4:
					heal.numheals -= 1


class Transformation(Ability):
	def __init__(self, wielder):
		desc = "+2 atk when wielder's life < 5"
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if self.wielder.life < 5:
			OffsetMod(self.wielder, attname='atk', offset=+2)

class UltimateShieldOfLight(Ability):
	def __init__(self, wielder):
		desc = "+2 atk to wielder and all your summoner's units only receive wounds from rolls of > 3."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		OffsetMod(self.wielder, attname='atk', offset=+2)
		if type(action) is Attack and subaction is 1 and action.target in self.wielder.owner.deck.units:
			action.rolltohit = 4


class ValiantDefender(Ability):
	def __init__(self, wielder):
		desc = "Forces enemy commons adjacent to wielder to not be able to move and to include wielder in their targets when attacking."
		super().__init__(wielder, desc=desc)

	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		for enemy in cardsfrom(self.wielder, spaces=1, type=Common, owners=self.wielder.owner.enemyteam):
			Mod(enemy, attname='movesleft', value=0)

		#copy pasted from protector except for agent being a Common.
		if type(action) is GetTargetCards and subaction is 3 and isinstance(action.agent, Common) and action.agent.owner in self.wielder.owner.enemyteam and isadjacent(action.agent, self.wielder):
			for card in action.lst.copy():
				protects = False
				if isinstance(card, Unit):
					for ability in card.abilities:
						if isinstance(ability, Protector) or isinstance(ability, ValiantDefender):
							protects = True
				if not protects:
					remove(card, action.lst)

# **********************************EVENTS***************************************
class Abolish(Event):
	def __init__(self, owner):
		desc = "Cancel an opponent's event card played during his event phase, and discard it."
		super().__init__(owner, desc=desc, faction=Vanguards)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return whoseturn in self.owner.enemyteam and phase is eventphase and type(action) is PlayEvent and subaction is 3

	def use(self, whoseturn, phase, subphase, action, subaction):
		def apply():
			self.owner.discard(action.target)
		action.apply = apply #TODO: cannot do this, because event might be used again later
		print(name(self.owner) + " abolished (cancelled and discarded) that event.")


class DivineProtection(Event):
	def __init__(self, owner):
		desc = "Cancel all wounds that would be inflicted on a controlled Common."
		super().__init__(owner, cost=1, desc=desc, faction=Vanguards)

	def isuseenabled(self, whoseturn, phase, subphase, action, subaction):
		return type(action) is Wound and subaction is 2 and action.count > 0 and action.target.owner is self.owner and isinstance(action.target, Common)

	def use(self, whoseturn, phase, subphase, action, subaction):
		action.count = 0


class DivineStrength(Event):
	def __init__(self, owner):
		desc = "Heal each of your Commons by 1."
		super().__init__(owner, desc=desc, faction=Vanguards)
	def use(self, whoseturn, phase, subphase, action, subaction):
		for card in cardsonboard(owners=[self.owner], type=Common):
			execute(Heal(healer=self.owner, target=card, numheals=1))


class HolyJudgment(Event):
	def __init__(self, owner):
		desc = "All your priests get +2 atk for 1 turn."
		super().__init__(owner, desc=desc, faction=Vanguards)
	def use(self, whoseturn, phase, subphase, action, subaction):
		for priest in cardsonboard(owners=[self.owner], type=Priest):
			OffsetMod(priest, attname='atk', offset=+2, turns=1)



class Intercession(Event):
	def __init__(self, owner):
		desc = "Transfer any number of wounds from a controlled Unit onto your summoner."
		super().__init__(owner, desc=desc, faction=Vanguards)
	def use(self, whoseturn, phase, subphase, action, subaction):
		unit = choosefrom(cardsonboard(owners=[self.owner], type=Unit))
		if unit is None:
			return False

		number = choosefrom([numwounds for numwounds in range(1, unit.maxlife - unit.life + 1)], 'Choose a number of wounds to transfer.')
		if number is 0:
			return False

		unit.life += number
		self.owner.life -= number


class StrongSpirits(Event):
	def __init__(self, owner):
		desc = "Move all Woeful Brothers from an opponent's discard pile into your magic pile."
		super().__init__(owner, desc=desc, faction=Vanguards)
	def use(self, whoseturn, phase, subphase, action, subaction):
		summoner = choosefrom(self.owner.enemyteam, 'Choose an opponent.')
		if summoner is None:
			return False

		if isempty([card for card in summoner.discardpile if isinstance(card, WoefulBrother)]):
			return False

		for card in summoner.discardpile.copy():
			if isinstance(card, WoefulBrother):
				move(card, self.owner.magicpile)



class TransformationEvent(Event):
	def __init__(self, owner):
		desc = "Add Ultimate Shield of Light ability (+2 atk, all your summoner's units only receive wounds from rolls of > 3) to your summoner for 1 turn."
		super().__init__(owner, desc=desc, faction=Vanguards)
	def use(self, whoseturn, phase, subphase, action, subaction):
		ListAddMod(self.owner.abilities, element=UltimateShieldOfLight(self.owner), turns=2)



# **********************************COMMONS***************************************

class Angel(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=Vanguards)
		Flight(wielder=self)

class CavalryKnight(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=2, maxlife=2, faction=Vanguards)
		Rider(wielder=self)

class GuardianKnight(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=1, maxlife=2, faction=Vanguards)
		Protector(wielder=self)

class HonorGuard(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=3, faction=Vanguards)
		Escort(wielder=self)

class Priest(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=1, cost=2, maxlife=2, faction=Vanguards)
		Healing(wielder=self)


class StalwartArcher(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=1, range=3, cost=2, maxlife=2, faction=Vanguards)
		HailOfArrows(wielder=self)

class WarriorAngel(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=2, maxlife=2, faction=Vanguards)
		Flight(wielder=self)

class WoefulBrother(Common):
	def __init__(self, owner):
		super().__init__(owner, atk=2, range=1, cost=2, maxlife=2, faction=Vanguards)
		SwiftManuever(wielder=self)

# **********************************CHAMPIONS***************************************

class Archangel(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=7, maxlife=6, faction=Vanguards)
		GreaterFlight(wielder=self)

class ColeenBrighton(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=6, maxlife=6, faction=Vanguards)
		ShieldOfLight(wielder=self)

class KalonLightbringer(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=7, maxlife=8, faction=Vanguards)
		Transformation(wielder=self)

class JacobEldwyn(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=3, cost=7, maxlife=5, faction=Vanguards)
		HeavensRain(wielder=self)

class LeahGoodwin(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=0, range=1, cost=3, maxlife=5, faction=Vanguards)
		BladeOfLight(wielder=self)

class MasterBullock(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=3, range=3, cost=7, maxlife=5, faction=Vanguards)
		MysticArts(wielder=self)

class RaechelLoveguard(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=1, range=3, cost=5, maxlife=4, faction=Vanguards)
		ArrowOfLight(wielder=self)

class SybilSwancott(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=4, range=3, cost=8, maxlife=3, faction=Vanguards)
		SybilsSpirit(wielder=self)

class ValentinaStoutheart(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=1, cost=8, maxlife=9, faction=Vanguards)
		ValiantDefender(wielder=self)


# **********************************SUMMONERS***************************************

class SamuelFarthen(Summoner):
	def __init__(self):
		setupdict = {(3, 3): Wall, (4, 2): WoefulBrother, (5, 2): WarriorAngel, (5, 1): SamuelFarthen, (6, 2): HonorGuard}
		events = [TransformationEvent(self) for count in range(3)] + [DivineProtection(self) for count in range(2)] + [Abolish(self) for count in range(2)] + [StrongSpirits(self) for count in range(2)]
		super().__init__(atk=2, range=1, maxlife=8, setupdict=setupdict, faction=Vanguards, events=events)
		ShieldOfLight(wielder=self)

class SeraEldwyn(Summoner):
	def __init__(self):
		setupdict = {(2, 1): StalwartArcher, (3, 1): Priest, (3, 2): GuardianKnight, (3, 3): Wall, (4, 1): SeraEldwyn, (4, 2): GuardianKnight, (5, 1): GuardianKnight}
		holyjudgments = [HolyJudgment(self) for count in range(3)]
		divinestrengths = [DivineStrength(self) for count in range(2)]
		summoningsurges = [SummoningSurge(self, faction=Vanguards) for count in range(2)]
		intercessions = [Intercession(self) for count in range(1)]
		aheroisborns = [AHeroIsBorn(self, faction=Vanguards) for count in range(1)]
		events = holyjudgments + divinestrengths + summoningsurges + intercessions + aheroisborns
		super().__init__(atk=2, range=3, maxlife=6, setupdict=setupdict, faction=Vanguards, events=events)
		GreaterHealing(wielder=self)

# **********************************DECKS***************************************
class DefaultVanguardsDeck(Deck):
	def __init__(self):
		summoner = SeraEldwyn()
		walls = [Wall(summoner, faction=Vanguards) for count in range(3)]
		commons = [StalwartArcher(summoner) for count in range(1)] + [GuardianKnight(summoner) for count in range(10)] + [Priest(summoner) for count in range(7)]
		champions = [LeahGoodwin(summoner), JacobEldwyn(summoner), ColeenBrighton(summoner)]
		super().__init__(summoner, commons, champions, walls)

class Vanguards(Faction):
	path = r'decks\vanguards\pics'
	commonclasses = [Angel, CavalryKnight, GuardianKnight, HonorGuard, Priest, StalwartArcher, WarriorAngel, WoefulBrother]
	championclasses = [Archangel, ColeenBrighton, KalonLightbringer, JacobEldwyn, LeahGoodwin, MasterBullock, RaechelLoveguard, SybilSwancott, ValentinaStoutheart]
	summonerclasses = [SamuelFarthen, SeraEldwyn]

defaultdeckclasses[Vanguards] = DefaultVanguardsDeck
add(Vanguards, factions)