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


class Explorer(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Explorer"
		self.description = "You may reveal a Province card from your hand. If you do, gain a Gold card, putting it into your hand." \
		                   "Otherwise, gain a Silver card, putting it into your hand"
		self.price = 5
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)

		selected = False
		if self.played_by.hand.get_count('Province') > 0:
			selection = yield self.played_by.select(1, 1, ['Yes', 'No'], "Reveal Province?")
			if selection[0] == 'Yes':
				self.played_by.gain_to_hand('Gold')
				selected = True

		if not selected:
			self.played_by.gain_to_hand('Silver')

		crd.Card.on_finished(self)