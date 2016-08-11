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


class Treasure_Map(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Treasure Map"
		self.price = 4
		self.description = ""
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		if self.played_by.hand.get_count('Treasure Map') > 0:
			selection = yield self.played_by.select(1, 1, ["Yes", "No"], "Would you like to trash "
			            "this and another copy of treasure map from hand to gain 4 Gold to the top of your deck?")
			if selection[0] == 'Yes':
				self.game.trash_pile.append(self.played_by.played_cards.pop())
				self.played_by.discard(['Treasure Map'], self.game.trash_pile)
				self.game.update_trash_pile()
				for i in range(0, 4):
					yield self.played_by.gain_to_deck("Gold", True, "")
				self.game.announce("-- gaining 4 " + self.game.log_string_from_title("Gold") + " to the top of their deck")

		else:
			self.game.announce('-- but there were no other copies of treasure map in hand')

		crd.Card.on_finished(self)


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


class Tactician(crd.Duration):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Tactician"
		self.price = 5
		self.description = "Discard your hand. " \
		                   "If you discarded any cards this way, then at the start of your next turn, \n" \
		                   "{} {} and {}".format(crd.format_draw(5), crd.format_buys(1), crd.format_actions(1))
		self.type = "Action|Duration"

	def play(self, skip=False):
		crd.Duration.play(self, skip)
		if len(self.played_by.hand):
			self.played_by.discard(crd.card_list_to_titles(self.played_by.hand.card_array()), self.played_by.discard_pile)

		else:
			self.game.announce("but there was nothing to discard")

		crd.Card.on_finished(self)

	def duration(self):
		crd.Duration.duration(self)
		drawn = self.played_by.draw(5)
		self.played_by.buys += 1
		self.played_by.actions += 1
		self.game.announce("-- drawing " + drawn + " and gaining +1 Buy, +1 Action")

# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------