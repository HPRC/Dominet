import sets.card as crd
import tornado.gen as gen

# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------


class Lighthouse(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Lighthouse"
		self.description = "{} Now and at the start of your next turn {}." \
		"While this is in play, you are unaffected by attack cards".format(crd.format_actions(1), crd.format_money(1))
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


# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------

class Caravan(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Caravan"
		self.price = 4
		self.description = "{} " \
		"Now and at the start of your next turn, {}".format(crd.format_actions(1), crd.format_draw(1))
		self.type = "Action|Duration"

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining +1 action and drawing {}".format(drawn))
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing {}".format(drawn))


# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Bazaar(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Bazaar"
		self.price = 5
		self.description = "{} {} {}".format(crd.format_draw(1), crd.format_actions(2), crd.format_money(1))
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 1
		self.played_by.actions += 2
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing {}, gaining +2 actions and gaining +$1".format(drawn))
		crd.Card.on_finished(self)

class Treasury(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Treasury"
		self.description = "{} {} {}" \
		                   "When you discard this card from play, if you didn't buy a Victory card this turn, " \
		                   "you may put this on top of your deck".format(crd.format_draw(1), crd.format_money(1), crd.format_actions(1))
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.balance += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing " + drawn + " and gaining +$1, +1 action")
		crd.Card.on_finished(self)

	@gen.coroutine
	def cleanup(self):
		total_victories_bought = len([x for x in self.played_by.bought_cards if 'Victory' in x.type])
		if total_victories_bought == 0:
			total_treasuries_played = len([x for x in self.played_by.played_inclusive if x.title == self.title])
			if total_treasuries_played > 1:
				selection = yield self.played_by.select(1, 1, [x for x in range(1, total_treasuries_played + 1)],
				                                        'Select the amount of treasuries you would like to return to the top of your deck')
				amount_to_return = selection[0]
			else:
				selection = yield self.played_by.select(1, 1, ['Yes', 'No'],
				                                        'Would you like to return Treasury to the top of your deck?')
				if selection[0] == 'Yes':
					amount_to_return = 1
				else:
					amount_to_return = 0

			count = 0
			for i in range(len(self.played_by.played_cards) - 1, -1, -1):
				if self.played_by.played_cards[i].title == 'Treasury':
					self.played_by.deck.append(self.played_by.played_cards[i])
					self.played_by.played_cards.pop(i)
					count += 1

				if count == amount_to_return:
					break

class Merchant_Ship(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Merchant Ship"
		self.price = 5
		self.description = "Now and at the start of your next turn {}".format(crd.format_money(2))
		self.type = "Action|Duration"

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		self.played_by.balance += 2
		self.game.announce("-- gaining +$2")
		crd.Duration.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		self.played_by.balance += 2
		self.game.announce("-- gaining +$2")

# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------