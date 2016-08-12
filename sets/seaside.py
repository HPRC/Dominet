import sets.card as crd
import tornado.gen as gen


class Lighthouse(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Lighthouse"
		self.description = "{} Now and at the start of your next turn {}. \
		While this is in play, you are unaffected by attack cards".format(crd.format_actions(1), crd.format_money(1))
		self.price = 2
		self.type = "Action|Duration"

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.balance += 1
		self.played_by.actions += 1
		self.played_by.protection = 9999
		self.game.announce("-- gaining +$1 and +1 action")
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		self.played_by.balance += 1
		self.game.announce("-- gaining +$1")
		self.played_by.protection = 0


class Wharf(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Wharf"
		self.description = "Now and at the start of your next turn " \
											 "{} {}.".format(crd.format_draw(2), crd.format_buys(1))
		self.price = 5
		self.type = "Action|Duration"

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		drawn = self.played_by.draw(2)
		self.played_by.buys += 1
		self.game.announce("-- gaining +1 Buy and drawing " + drawn + " cards")
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		drawn = self.played_by.draw(2)
		self.played_by.buys += 1
		self.game.announce(" -- gaining +1 Buy and drawing " + drawn + " cards")
