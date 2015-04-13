import card as crd


# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------

class Monument(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Monument"
		self.description = "+$2\n +1 VP token."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.vp += 1
		self.game.announce("-- gaining +$2 and +1 VP")
		crd.Card.on_finished(self)


class Workers_Village(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Workers Village"
		self.description = "+1 Card; +2 Actions, +1 Buy"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2
		self.played_by.buys += 1
		drawn = self.played_by.draw(1)

		self.game.announce("-- drawing " + drawn + " cards and gaining 2 actions and 1 buy")

		self.played_by.update_hand()
		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Counting_House(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Counting House"
		self.description = "Look through your discard pile, reveal any number of Copper cards from it, and put them into your hand."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)

		discarded_coppers = self.played_by.get_card_count_in_list('Copper', self.played_by.discard_pile)

		self.game.announce("-- removing " + str(discarded_coppers) + " coppers from their discard and putting them in hand.")
		for i in range(discarded_coppers - 1, -1, -1): # loop through discard pile backwards to in place remove coppers
			if self.played_by.discard_pile[i].title == "Copper":
				copper = self.played_by.discard_pile.pop(i)
				self.played_by.hand.add(copper)
		self.played_by.update_hand()
		crd.Card.on_finished(self)


class Mint(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Mint"
		self.description = "You may reveal a Treasure card from your hand. Gain a copy of it.\n" \
		                   "When you buy this, trash all Treasures you have in play."
		self.value = 0
		self.price = 5
		self.type = "Treasure"

	def play(self, skip=False):
		crd.Card.play(self, skip)

	def on_purchase(self):
		self.played_by = "me"


class Mountebank(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Mountebank"
		self.description = "+$2\nEach other player may discard a Curse. If he doesn't, he gains a Curse and a Copper."
		self.price = 5
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.AttackCard.play(self, skip)
		self.played_by.balance += 2
		self.played_by.update_resources()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		crd.AttackCard.get_next(self, self.played_by)

	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			if player.hand.get_card("Curse"):
				def post_select_on(selection, player=player):
					self.post_select(selection, player)
			else:
				player.gain("Copper")
				player.gain("Curse")

	# def post_select(self, selection, player):
	 	# if selection[0] == "Yes":
	 	# 	# player.hand.


# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------

# --------------------------------------------------------
# ------------------------ 7 Cost ------------------------
# --------------------------------------------------------

class Expand(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Expand"
		self.description = "Trash a card from your hand. Gain a card costing up to $3 more than the trashed card."
		self.price = 7
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		                      "select card to expand")
		self.played_by.update_resources()
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.discard(selection, self.game.trash_pile)
		card_trashed = self.game.card_from_title(selection[0])
		self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
		self.played_by.select_from_supply(card_trashed.price + 3, False)

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.update_hand()

	def post_gain(self, selected):
		self.played_by.gain(selected[0])
		crd.Card.on_finished(self, False, False)


# --------------------------------------------------------
# ------------------------ 8 Cost ------------------------
# --------------------------------------------------------
