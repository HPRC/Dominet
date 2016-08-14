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

class Sea_Hag(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Sea Hag"
		self.description = "Each other player discards the top card of their deck, " \
		                   "then gains a Curse putting it on top of their deck"
		self.price = 4
		self.type = "Action|Attack"

	@gen.coroutine
	def play(self, skip=False):
		crd.AttackCard.play(self, skip)
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	@gen.coroutine
	def attack(self):
		yield self.fire(self.played_by.get_left_opponent())

	@gen.coroutine
	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			topdeck = player.topdeck()
			player.discard([topdeck.title], player.discard_pile)

			self.game.announce('-- ' + player.name_string() + ' discards ' + self.game.log_string_from_title(topdeck.title))
			player.gain_to_deck('Curse')

		yield crd.AttackCard.get_next(self, player)
