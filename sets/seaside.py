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


class Island(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = 'Island'
		self.description = ''
		self.price = 4
		self.type = 'Action|Victory'
		self.vp = 2

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		                                        'Select a card to banish on the island')
		self.played_by.discard(selection, self.played_by.island_pile)
		self.game.announce('-- banishing ' + self.game.log_string_from_title(selection[0]) + ' to the island')
		island = self.played_by.played_cards.pop()
		self.played_by.island_pile.append(island)
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(
			["<span class='label label-action-victory'>", self.title + "s</span>" if plural else self.title, "</span>"])
