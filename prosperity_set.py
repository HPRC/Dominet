import card as crd
import math

# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------


class Loan(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Loan"
		self.description = "Worth $1\n" \
		                   "When you play this, reveal cards from your deck until you reveal a Treasure." \
		                   "Discard it or trash it. Discard the other cards."
		self.price = 3
		self.value = 1
		self.type = "Treasure"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

		revealed_treasure = False
		total_deck_count = len(self.played_by.discard_pile) + len(self.played_by.deck)
		discarded = list()
		while revealed_treasure is not True and len(discarded) < total_deck_count:
			topdeck = self.played_by.topdeck()
			if "Treasure" in topdeck.type:
				revealed_treasure = True
				self.played_by.deck.append(topdeck)
			else:
				self.played_by.discard_pile.append(topdeck)
				discarded.append(topdeck.title)

		if len(discarded) > 0:
			self.game.announce("-- discarding " + ", ".join(
				list(map(lambda x: self.game.log_string_from_title(x), discarded))))

		if revealed_treasure is True:
			self.game.announce("-- revealing " + topdeck.log_string())

			self.played_by.select(1, 1, ["Discard", "Trash"], "Discard or Trash " + topdeck.title)
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select
		else:
			self.game.announce("-- but could not find any treasures in his or her deck.")
			crd.Card.on_finished(self)

	def post_select(self, selection):
		topdeck = self.played_by.topdeck()
		if selection[0] == "Discard":
			self.played_by.discard_pile.append(topdeck)
			self.played_by.update_hand()
			self.game.announce("-- discarding " + topdeck.log_string())
		else:
			self.game.trash_pile.append(topdeck)
			self.game.update_trash_pile()
			self.game.announce("-- trashing " + topdeck.log_string())

		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------


class Bishop(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Bishop"
		self.description = "+$1; +1 VP token Trash a card from your hand.  +VP tokens equal to half its cost in coins" \
		                   ", rounded down. Each other player may trash a card from his hand."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 1
		self.played_by.vp += 1

		self.game.announce("-- gaining +$1 and +1 VP")
		self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Choose a card to trash")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.vp_trash_select

	def vp_trash_select(self, selection):
		trash = self.played_by.hand.extract(selection[0])
		half_vp = math.floor(trash.price / 2)
		self.played_by.vp += half_vp
		self.game.trash_pile.append(trash)
		self.game.update_trash_pile()

		self.played_by.update_hand()

		self.game.announce("-- trashing " + trash.log_string() + " gaining " + str(half_vp) + " VP")

		self.played_by.wait("Waiting for other players to trash")
		for i in self.played_by.get_opponents():
			self.played_by.waiting["on"].append(i)

		self.get_next(self.played_by)

	def get_next(self, player):
		next_player_index = (self.game.players.index(player) + 1) % len(self.game.players)
		next_player = self.game.players[next_player_index]
		if next_player == self.played_by:
			crd.Card.on_finished(self)
		else:
			def trash_select_cb(selection, next_player=next_player):
				self.trash_select(selection, next_player)

			next_player.select(1, 1, crd.card_list_to_titles(next_player.hand.card_array()) + ["None"],
			                   "Choose a card to trash")
			next_player.waiting["on"].append(next_player)
			next_player.waiting["cb"] = trash_select_cb

	def trash_select(self, selection, player):
		if selection[0] != "None":
			trash = player.hand.extract(selection[0])
			self.game.trash_pile.append(trash)
			self.game.update_trash_pile()
			player.update_hand()
			self.game.announce("-- " + player.name + " trashes " + trash.log_string())
		self.get_next(player)


class Monument(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Monument"
		self.description = "+$2\n +1 VP"
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

class City(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "City"
		self.description = "+1 Card; +2 Actions " \
		                   "If there are one or more empty Supply piles, +1 Card. If there are two or more, +$1 and +1 Buy."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2

		if self.game.empty_piles >= 1:
			drawn = self.played_by.draw(2)
		else:
			drawn = self.played_by.draw(1)

		drawn = "and drawing " + drawn

		if self.game.empty_piles >= 2:
			self.played_by.buys += 1
			self.played_by.balance += 1
			drawn = "+1 buy and +$1 " + drawn

		self.game.announce("-- gaining 2 actions " + drawn)
		self.played_by.update_hand()

		crd.Card.on_finished(self)


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
		for i in range(discarded_coppers - 1, -1, -1):  # loop through discard pile backwards to in place remove coppers
			if self.played_by.discard_pile[i].title == "Copper":
				copper = self.played_by.discard_pile.pop(i)
				self.played_by.hand.add(copper)
		self.played_by.update_hand()
		crd.Card.on_finished(self)


class Mint(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Mint"
		self.description = "You may reveal a Treasure card from your hand. Gain a copy of it.\n" \
		                   "When you buy this, trash all Treasures you have in play."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		treasures = self.played_by.hand.get_cards_by_type("Treasure", True)
		treasures = dedupe_list(treasures)

		# perhaps write an auto_select method for lists?
		if len(treasures) == 0:
			self.game.announce("-- but there were no treasures to reveal")
			crd.Card.on_finished(self, False, False)
		elif len(treasures) == 1:
			self.reveal(treasures)
		else:
			self.played_by.select(1, 1, treasures, "Choose a card to reveal")

			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.reveal

	def reveal(self, selection):
		self.game.announce("-- revealing " + self.game.log_string_from_title(selection[0]) + " gaining a copy of it.")
		self.played_by.gain(selection[0])
		crd.Card.on_finished(self, False, False)

	def on_buy(self):
		trashed_treasures = list()
		for i in range(len(self.played_by.played) - 1, -1, -1):
			if self.played_by.played[i].type == 'Treasure':
				trashed_treasures.append(self.played_by.played.pop(i))
		announce_string = ", ".join(list(map(lambda x: self.game.log_string_from_title(x.title), trashed_treasures)))

		self.game.announce("-- trashing " + announce_string)

		for card in trashed_treasures:
			self.game.trash_pile.append(card)

		self.game.update_trash_pile()


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
			if "Curse" in player.hand:
				def post_select_on(selection, player=player):
					self.post_select(selection, player)
				player.select(1, 1, ["Yes", "No"], "Discard a curse?")
				self.played_by.wait("Waiting for other players to choose")
				player.waiting["on"].append(player)
				player.waiting["cb"] = post_select_on

			else:
				player.gain("Copper")
				player.gain("Curse")
				crd.AttackCard.get_next(self, player)

	def post_select(self, selection, player):
		if selection[0] == "Yes":
			curse = player.hand.extract("Curse")
			player.update_hand()
			player.discard_pile.append(curse)
			self.game.announce("-- " + player.name_string() + " discards a " + curse.log_string())
		else:
			player.gain("Copper")
			player.gain("Curse")

		crd.AttackCard.get_next(self, player)


class Vault(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Vault"
		self.description = "+2 Cards\nDiscard any number of cards. +$1 per card discarded. " \
		                   "Each other player may discard 2 cards. If he does, he draws a card."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.played_by.update_hand()
		self.game.announce("-- drawing " + drawn)

		self.played_by.select(None, len(self.played_by.hand.card_array()),
		                      crd.card_list_to_titles(self.played_by.hand.card_array()), "Discard any number of cards")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_discard

	def post_discard(self, selection):
		self.played_by.discard(selection, self.played_by.discard_pile)

		self.played_by.update_hand()
		self.played_by.balance += len(selection)
		self.game.announce("-- discarding " + str(len(selection)) +
		                   ", gaining +$" + str(len(selection)))

		self.played_by.wait("Waiting for other players to discard")
		for i in self.played_by.get_opponents():
			self.played_by.waiting["on"].append(i)
		self.get_next(self.played_by)

	def get_next(self, player):
		next_player_index = (self.game.players.index(player) + 1) % len(self.game.players)
		next_player = self.game.players[next_player_index]
		if next_player == self.played_by:
			crd.Card.on_finished(self)
		else:
			def discard_choice_cb(selection, next_player=next_player):
					self.discard_choice(selection, next_player)

			next_player.select(1, 1, ["Yes", "No"], "Discard 2 cards to draw 1?")
			next_player.waiting["on"].append(next_player)
			next_player.waiting["cb"] = discard_choice_cb

	def discard_choice(self, selection, player):
		if selection[0] != "Yes":
			self.get_next(player)
		else:
			def discard_select_cb(selection, player=player):
				self.discard_select(selection, player)

			player.select(min(len(player.hand.card_array()), 2), 2, crd.card_list_to_titles(player.hand.card_array()), "Discard up to 2")
			self.played_by.wait("Waiting for " + player.name + " to discard")
			self.played_by.waiting["on"].append(player)
			player.waiting["on"].append(player)
			player.waiting["cb"] = discard_select_cb

	def discard_select(self, selection, player):
		player.discard(selection, player.discard_pile)
		self.game.announce("-- discarding " + str(len(selection)) + " cards")

		if len(selection) >= 2:
			drawn = player.draw(1)
			player.update_hand()
			self.game.announce("-- drawing " + drawn)
		self.get_next(player)


class Venture(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Venture"
		self.description = "Worth $1\nWhen you play this, reveal cards from your deck until you reveal a Treasure. " \
		                   "Discard the other cards. Play that Treasure."
		self.price = 5
		self.value = 1
		self.type = "Treasure"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

		revealed_treasure = False
		total_deck_count = len(self.played_by.discard_pile) + len(self.played_by.deck)
		discarded = list()
		while revealed_treasure is not True and len(discarded) < total_deck_count:
			topdeck = self.played_by.topdeck()
			if "Treasure" in topdeck.type:
				revealed_treasure = True
			else:
				self.played_by.discard_pile.append(topdeck)
				discarded.append(topdeck.title)

		if len(discarded) > 0:
			self.game.announce("-- discarding " + ", ".join(
				list(map(lambda x: self.game.log_string_from_title(x), discarded))))

		if revealed_treasure is True:
			self.game.announce("-- revealing " + topdeck.log_string())
			self.game.announce("-- " + self.played_by.name_string() + " played " + topdeck.log_string())
			topdeck.play(True)
		else:
			self.game.announce("-- but could not find any treasures in his or her deck.")
		crd.Card.on_finished(self, waiting_cleanup=False)

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


class Forge(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Forge"
		self.description = "Trash any number of cards from your hand." \
		                   "Gain a card with cost exactly equal to the total cost in coins of the trashed cards."
		self.price = 7
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(None, len(self.played_by.hand.card_array()), crd.card_list_to_titles(self.played_by.hand.card_array()), "Trash any number of cards")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.trash_select

	def trash_select(self, selection):
		trash_sum = 0
		trashed = list()
		for card in selection:
			trash_card = self.played_by.hand.extract(card)
			trashed.append(trash_card.title)
			trash_sum += trash_card.get_price()
			self.game.trash_pile.append(trash_card)

		announce_string = list(map(lambda x: self.game.card_from_title(x).log_string(), selection))

		self.game.update_trash_pile()
		self.game.announce(self.played_by.name_string() + " trashes " + ", ".join(announce_string) + " to gain a card with cost " + str(trash_sum))

		if self.game.supply.pile_contains(trash_sum):
			self.played_by.select_from_supply(price_limit=trash_sum, equal_only=True, optional=False)
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.gain_select
		else:
			self.game.announce("-- but there are no cards that cost " + str(trash_sum))
			crd.Card.on_finished(self)

	def gain_select(self, selection):
		self.played_by.gain(selection[0])
		self.game.announce("-- gaining " + self.game.card_from_title(selection[0]).log_string())
		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 8 Cost ------------------------
# --------------------------------------------------------


def dedupe_list(lst):
	unique_cards = {}
	for card in lst:
		if card.title not in unique_cards:
			unique_cards[card.title] = card

	return list(map(lambda x: x, unique_cards))