class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None

	def play(self):
		raise NotImplementedError


class Copper(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Copper"
		self.type = "Money"

	def play(self):
		self.game.announce("<b>" + self.played_by.name + "</b> played " + self.title)
		self.played_by.balance += 1

class Estate(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Estate"
		self.type = "Victory"

	def play(self):
		return


