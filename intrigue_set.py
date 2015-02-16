import card as crd


class Courtyard(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Courtyard"
		self.description = "+3 Cards\n Put a card from your hand on top of your deck."
		self.price = 2
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.draw(3)
		self.game.announce("-- drawing 3 cards")
		self.played_by.update_resources()
		self.played_by.update_hand()
		self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Choose a card to put back on top of your deck.")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.game.announce("-- " + self.game.log_string_from_title(selection[0]) + " is placed on top of the deck.")
		self.played_by.discard(selection, self.played_by.deck)
		crd.Card.on_finished(self, True, False)


class Pawn(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Pawn"
		self.description = "Choose two:\n +$1, +1 Buy, +1 Action, +1 Card"
		self.price = 2
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(2, 2, ["+$1", "+1 Action", "+1 Buy", "+1 Card"], "Choose Two:")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		announcements = []
		if "+$1" in selection:
			self.played_by.balance += 1
			announcements.append("+$1")

		if "+1 Action" in selection:
			self.played_by.actions += 1
			announcements.append("+1 action")

		if "+1 Buy" in selection:
			self.played_by.buys += 1
			announcements.append("+1 buy")

		if "+1 Card" in selection:
			self.played_by.draw(1)
			announcements.append("drawing 1 card")

		self.game.announce("-- gaining " + " and ".join(announcements))

		crd.Card.on_finished(self)


class Great_Hall(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Great Hall"
		self.description = "+1 Card\n +1 Action\n +1 VP\n"
		self.price = 3
		self.vp = 1
		self.type = "Victory|Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining +1 action and drawing " + drawn)
		crd.Card.on_finished(self)


class Shanty_Town(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Shanty Town"
		self.description = "+2 Actions\n Reveal your hand.  If you have no Action cards in hand, +2 Cards."
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2

		self.game.announce("-- gaining 2 actions")

		revealed_cards = self.played_by.hand.card_array()
		action_cards = 0
		for card in revealed_cards:
			if "Action" in card.type:
				action_cards += 1

		self.game.announce(self.played_by.name_string() + " reveals " + str(self.played_by.hand.reveal_string())
								+ " containing " + str(action_cards) + " action cards.")
		if action_cards == 0:
			self.played_by.draw(2)
			self.game.announce("-- drawing 2 cards")

		crd.Card.on_finished(self)


class Steward(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Steward"
		self.description = "Choose one:\n +2 Cards, or +$2, or trash exactly 2 cards from your hand."
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(1, 1, ["+$2", "+2 Cards", "Trash 2 cards from hand"], "Choose One:")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		if "+$2" in selection:
			self.played_by.balance += 2
			self.game.announce("-- gaining +$2")
			crd.Card.on_finished(self, False)

		elif "+2 Cards" in selection:
			self.played_by.draw(2)
			self.game.announce("-- drawing 2 cards")
			crd.Card.on_finished(self)
		elif "Trash 2 cards from hand" in selection:
			self.game.announce("-- choosing to trash 2 cards from hand")

			if len(self.played_by.hand) > 2 and not self.played_by.hand.is_homogeneous():
				self.played_by.select(2, 2, crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to trash")
				self.played_by.waiting["on"].append(self.played_by)
				self.played_by.waiting["cb"] = self.trash_select
			else:
				card_selection = crd.card_list_to_titles(self.played_by.hand.auto_select(2))
				self.trash_select(card_selection)

	def trash_select(self, selection):
		if len(selection) == 0:
			selection_string = "nothing"
		else:
			selection_string = ", ".join(list(map(lambda x: self.game.log_string_from_title(x), selection)))
		self.game.announce(self.played_by.name_string() + " trashes " + selection_string)
		self.played_by.waiting["cb"] = None
		self.played_by.discard(selection, self.game.trash_pile)
		crd.Card.on_finished(self, True, False)


class Baron(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Baron"
		self.description = "+1 Buy\n You may discard an Estate card, if you do +$4\n Otherwise, gain an Estate card."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.buys += 1
		self.game.announce("-- gaining +1 buy")

		if "Estate" in self.played_by.hand:
			self.played_by.select(1, 1, ["Yes", "No"], "Would you like to discard an Estate for +$4?")
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select

		else:
			self.played_by.gain("Estate")

	def post_select(self, selection):
		if "Yes" in selection:
			self.played_by.balance += 4
			self.game.announce("-- discarding an " + self.played_by.hand['Estate'][0].log_string() + " and gaining +$4 ")
			self.played_by.discard(["Estate"], self.played_by.discard_pile)
			crd.Card.on_finished(self)
		else:
			self.played_by.gain("Estate")
		crd.Card.on_finished(self)


class Conspirator(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Conspirator"
		self.description = "+$2\n If you’ve played 3 or more Actions this turn (counting this): +1 Card; +1 Action."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2

		played_cards = self.played_by.played
		played_action_cards = 0
		announcement = "-- gaining $2"
		for data in played_cards:
			if "Action" in data.type:
				played_action_cards += 1

		if played_action_cards >= 3:
			self.played_by.actions += 1
			self.played_by.draw(1)
			announcement += " and drawing a card and gaining +1 action"

		self.game.announce(announcement)

		crd.Card.on_finished(self)


class Nobles(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Nobles"
		self.description = "2 Victory Points\n Choose one: +3 Cards; or +2 Actions."
		self.price = 6
		self.vp = 2
		self.type = "Victory|Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)

		self.played_by.select(1, 1, ["+2 Actions", "+3 Cards"], "Choose one: +3 Cards; or +2 Actions.")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		if "+2 Actions" in selection:
			self.played_by.actions += 2
			self.game.announce("-- gaining 2 actions")

		else:
			drawn = self.played_by.draw(3)
			self.game.announce("-- drawing " + drawn)

		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", "Nobles</span>" if plural else self.title, "</span>"])
