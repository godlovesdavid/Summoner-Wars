from summonerwars.menus import *


# **********************************ABILITIES***************************************
class Grapple(Ability):
	def __init__(self, wielder):
		desc = "Choose a Common at turn end. That Common cannot move nor attack until your next turn's begin. If still adjacent to that Common by that time, wound it by 1."
		super().__init__(wielder, desc=desc)
		self.grappled = None
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		if whoseturn is self.wielder.owner:
			#wound grappled unit.
			if phase is drawphase and subphase is 1 and self.grappled is not None:
				target = self.grappled	#must be done to prevent recursion
				self.grappled = None
				self.wielder.wound(target)

			#choose a unit to grapple at turn end.
			elif phase is magicphase and subphase is 3 and not isempty(cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam, type=Common)):
				unit = choosefrom(cardsfrom(self.wielder, spaces=1, owners=self.wielder.owner.enemyteam, type=Common), msg='Choose a unit next to ' + name(self.wielder) + ' to grapple.')
				if unit is None:
					return False

				self.grappled = unit

		if self.grappled is not None:
			Mod(self.grappled, attname='movesleft', value=0)
			Mod(self.grappled, attname='attacksleft', value=0)



class Wisdom(Ability):
	def __init__(self, wielder):
		desc = "When drawing, can draw up to 7 cards, as long as wielder is on the field."
		super().__init__(wielder, desc=desc)
	def passiveuse(self, whoseturn, phase, subphase, action, subaction):
		Mod(self.wielder.owner, attname='allowedinhand', value=7)


# **********************************CHAMPIONS***************************************

class Kogar(Champion):
	def __init__(self, owner):


		super().__init__(owner=owner, atk=2, range=1, cost=6, maxlife=6, faction=Mercenaries)
		Grapple(wielder=self)

class Magos(Champion):
	def __init__(self, owner):
		super().__init__(owner=owner, atk=2, range=3, cost=6, maxlife=5, faction=Mercenaries)
		Wisdom(wielder=self)


class Mercenaries(Faction):
	path = r'decks\mercenaries\pics'
	commonclasses = []
	championclasses = [Kogar, Magos]
	summonerclasses = []
