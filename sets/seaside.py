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


class Pearl_Diver(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Pearl Diver"
		self.description = "{} {}" \
											 "While this is in play, you are unaffected by attack cards".format(crd.format_draw(1), crd.format_actions(1))
		self.price = 2
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("Drawing " + drawn + " cards and gaining + 1 actions")

		if len(self.played_by.deck) == 0:
			self.played_by.shuffle_discard_to_deck()

		bottom_card = self.played_by.deck[0].title
		selection = yield self.played_by.select(1, 1, ["Yes", "No"], "The bottom card of your deck is " + bottom_card.title() + " "
								"Move it to the top of your deck?")

		if selection[0] == "Yes":
			bottom_card = self.played_by.deck.pop(0)
			self.played_by.deck.append(bottom_card)

		crd.Card.on_finished(self)