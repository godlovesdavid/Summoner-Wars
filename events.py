from summonerwars.menus import *

class AHeroIsBorn(Event):
	def __init__(self, owner, faction):
		desc = "Put a Champion from your draw pile into your hand, reveal it, and shuffle your draw pile."
		super().__init__(owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		card = choosefrom([card for card in self.owner.drawpile if isinstance(card, Champion)], 'Choose a Champion from your draw pile.')
		if card is None:
			return False

		#TODO: show card to players

		move(card, self.owner.hand)


class MagicDrain(Event):
	def __init__(self, owner, faction):
		desc = "Move up to 2 cards from an opponent's magic pile to your magic pile if you have less units on field than he does."
		super().__init__(owner, desc=desc, faction=faction)
	def use(self, whoseturn, phase, subphase, action, subaction):
		#choose opponent with less units than you.
		opponent = choosefrom([summoner for summoner in self.owner.enemyteam if len(cardsonboard(owners=[summoner], type=Unit)) > len(cardsonboard(owners=[self.owner], type=Unit))], msg="Choose an opponent with more units than you.")
		if opponent is None:
			return False

		# got this far? Now move from magic pile to magic pile.
		count = 0
		while count < 2 and len(opponent.magicpile) > 0:
			move(top(opponent.magicpile), self.owner.magicpile)
			count += 1

		if count is 0:
			return False

		print('Moved', count, 'cards from their magic pile to your magic pile.')



class SummoningSurge(Event):
	def __init__(self, owner, faction):
		desc = "If any opponent has more units on the field than you, move up to 3 cards from your discard into your magic pile. You can then summon units."
		super().__init__(owner, desc=desc, faction=faction)

	def use(self, whoseturn, phase, subphase, action, subaction):
		#should have a card in discard pile.
		if isempty(self.owner.discardpile):
			return False

		# cannot proceed if no opponent has less units than you.
		ok = False
		for opponent in self.owner.enemyteam:
			if len(cardsonboard(owners=[opponent], type=Unit)) > len(cardsonboard(owners=[self.owner], type=Unit)):
				ok = True
				break
		if not ok:
			return False

		# move from discard to magic pile. #TODO: make moving any cards optional?
		count = 0
		while count < 3 and len(self.owner.discardpile) > 0:
			move(top(self.owner.discardpile), self.owner.magicpile)
			count += 1
		print('Moved', count, 'cards from discard to magic pile.')


		# let user summon things.
		while len(self.owner.hand) > 0:
			choice = choosefrom(summonablecards(self.owner), msg='Choose a unit to summon.')
			if choice is None:
				break

			cell = choosefrom(choice.getsummoncells())
			if cell is None:
				continue
			self.owner.summon(choice, cell)


