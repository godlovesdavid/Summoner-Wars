from summonerwars.menus import *

#override normal cell-is-moveable-to conditions.
def ismoveable(cell):
	for card in cell:
		if not isinstance(card, VineWall):
			return False


# special wall of the swamp orcs.
class VineWall(Wall):
	def __init__(self, owner):
		cardpic = Image.open(r"pics\swamporcs\vinewallcard.ppm")
		Wall.__init__(self, owner, cardpic)
		self.maxlife = 2
		self.life = self.maxlife

