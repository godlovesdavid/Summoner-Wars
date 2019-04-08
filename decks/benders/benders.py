from summonerwars.menus import *


# **********************************EVENTS***************************************

# **********************************COMMONS***************************************

# **********************************CHAMPIONS***************************************
class Capture(Ability):
	def __init__(self, wielder):
		super().__init__(wielder)
		# when killed something, take control of it.
		def killcleanup(card):
			if isinstance(card, Unit):
				card.owner = self.owner
				card.life = card.maxlife
			else:
				Common.killcleanup(wielder, card)
		wielder.killcleanup = killcleanup
	def __del__(self):
		self.wielder.killcleanup = Unit.killcleanup

class Tacula(Champion):
	def __init__(self, owner):
		Champion.__init__(self, owner=owner)
		add(Capture(self), self.abilities)

# **********************************SUMMONER***************************************

# add(, SUMMONERS)