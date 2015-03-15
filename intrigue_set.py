import card as crd


# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------

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
		self.played_by.update_deck_size()
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
			drawn = self.played_by.draw(1)
			announcements.append("drawing " + drawn)

		self.game.announce("-- gaining " + " and ".join(announcements))

		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

class Great_Hall(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Great Hall"
		self.description = "+1 Card\n +1 Action\n 1 VP\n"
		self.price = 3
		self.vp = 1
		self.type = "Action|Victory"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining +1 action and drawing " + drawn)
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default-success'>", self.title + "s</span>" if plural else self.title, "</span>"])

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
				card_selection = self.played_by.hand.auto_select(2, True)
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


class Swindler(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Swindler"
		self.description = "+$2\n Each other player trashes the top card of his deck and gains a card with the same cost that you choose."
		self.price = 3
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.game.announce("-- gaining +$2")
		self.played_by.update_resources()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		crd.AttackCard.get_next(self, self.played_by)

	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			topdeck = player.topdeck()
			if topdeck != None:
				player.game.trash_pile.append(topdeck)
				player.game.update_trash_pile()
				self.game.announce(self.played_by.name_string() + " trashes " + self.game.log_string_from_title(topdeck.title)
				                   + " from the top of " + player.name_string() + "'s deck.")

				def post_select_on(selection, player=player):
					self.post_select(selection, player)

				self.played_by.select_from_supply(topdeck.price, True)
				self.played_by.waiting["on"].append(self.played_by)
				self.played_by.waiting["cb"] = post_select_on
			else:
				self.game.announce(player.name_string() + " has no cards to Swindle.")
				crd.AttackCard.get_next(self, player)

	def post_select(self, selection, victim):
		victim.gain(selection)
		crd.AttackCard.get_next(self, victim)

class Wishing_Well(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Wishing Well"
		self.description = "+1 Card; +1 Action\n Name a card, then reveal the top card of your deck. If it is the named card, put it in your hand."
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.draw(1)
		self.played_by.update_resources()
		self.played_by.update_hand()
		self.game.announce("-- gaining +1 action and drawing a card")

		self.played_by.select_from_supply(allow_empty=True)
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		topdeck = self.played_by.topdeck()
		self.game.announce("-- wishing for a " + self.game.log_string_from_title(selection))
		if topdeck:
			if topdeck.title == selection:
				self.played_by.hand.add(topdeck)
				announcement = ", adding it to their hand."	
			else:
				self.played_by.deck.append(topdeck)
				announcement = " returning it to the top of their deck."
			self.game.announce("-- revealing " + topdeck.log_string() + announcement)
		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------

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
			crd.Card.on_finished(self, False)

	def post_select(self, selection):
		if "Yes" in selection:
			self.played_by.balance += 4
			self.game.announce("-- discarding an " + self.played_by.hand.data['Estate'][0].log_string() + " and gaining +$4 ")
			self.played_by.discard(["Estate"], self.played_by.discard_pile)
		else:
			self.played_by.gain("Estate")
		crd.Card.on_finished(self)

class Bridge(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Bridge"
		self.description = "+1 Buy, +$1,\n All cards (including ones in player's hands) cost $1 less this turn, but not less than $0."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.buys += 1
		self.played_by.balance += 1
		self.game.price_modifier -= 1
		self.game.update_all_prices()
		self.game.announce("-- gaining 1 buy, $1")
		crd.Card.on_finished(self, False, True)

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

class Coppersmith(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Coppersmith"
		self.description = "Coppers produce an extra $1 this turn."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		for card in self.played_by.all_cards():
			if card.title == "Copper":
				card.value += 1
		crd.Card.on_finished(self)

	def cleanup(self):
		for card in self.played_by.all_cards():
			if card.title == "Copper":
				card.value -= 1

class Ironworks(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Ironworks"
		self.description = "Gain a card costing up to $4.\n If it is an… Action card, +1 Action. Treasure card, +$1. Victory card, +1 Card."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.game.announce("Gain a card costing up to $4")

		self.played_by.select_from_supply(4)
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		card = self.game.card_from_title(selection)
		self.played_by.gain(selection, True)
		effects = []
		if "Action" in card.type:
			self.played_by.actions += 1
			effects.append("gaining 1 action")
		if "Treasure" in card.type:
			self.played_by.balance += 1
			effects.append("gaining +$1")
		if "Victory" in card.type:
			self.played_by.draw(1)
			effects.append("drawing a card")
		if not card.type == "Curse":
			self.game.announce("-- " + " and ".join(effects))
		crd.Card.on_finished(self)

class Mining_Village(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Mining Village"
		self.description = "+1 Card, +2 Actions\n You may trash this card immediately to gain $2."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining 2 actions and drawing " + drawn)
		self.played_by.update_hand()
		self.played_by.select(1, 1, ["Yes", "No"], "Trash Mining Village for $2?")

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		if "Yes" in selection:
			if len(self.game.trash_pile) > 0 and self.game.trash_pile[-1] == self:
				self.game.announce("-- tries to trash " + self.log_string() + " but it was already trashed")
			elif self in self.played_by.played:
				self.game.announce("-- trashing " + self.log_string() + " to gain $2")
				self.played_by.balance += 2
				self.game.trash_pile.append(self.played_by.played.pop())
				self.game.update_trash_pile()
		crd.Card.on_finished(self)

# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------


class Duke(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Duke"
		self.description = "Worth 1 Victory Point per Duchy you have."
		self.price = 5
		self.vp = 0
		self.type = "Victory"

	def get_vp(self):
		hand_count = self.played_by.hand.get_count('Duchy')
		deck_count = self.played_by.get_card_count_in_list('Duchy', self.played_by.deck)
		discard_count = self.played_by.get_card_count_in_list('Duchy', self.played_by.discard_pile)
		return int(hand_count + deck_count + discard_count)


class Torturer(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Torturer"
		self.description = "+3 Cards\n Each other player chooses one: he discards 2 cards; or he gains a Curse card, putting it in his hand."
		self.price = 5
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.draw(3)
		self.played_by.update_hand()
		self.played_by.update_resources()
		self.game.announce("-- drawing 3 cards.")
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		crd.AttackCard.get_next(self, self.played_by)

	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			def post_select_on(selection, player=player):
				self.post_select(selection, player)

			player.select(1, 1, ["Discard 2 cards", "Gain a Curse"], "Choose one:")
			self.played_by.wait("Waiting for other players to choose")
			#Here we add the player to our waiting list twice so that we keep waiting between
			#choices (if they choose discard 2 it'll keep waiting)
			self.played_by.waiting["on"].append(player)
			self.played_by.waiting["on"].append(player)
			player.waiting["on"].append(player)
			player.waiting["cb"] = post_select_on

	def post_select(self, selection, victim):
		if selection[0] == 'Gain a Curse':
			#we call update_wait manually to update the torturer and override the second wait
			victim.update_wait()
			victim.gain_to_hand('Curse')
			victim.update_hand()
			crd.AttackCard.get_next(self, victim)
		else:
			discard_selection = victim.hand.auto_select(2, True)
			if discard_selection:
				victim.discard(discard_selection, victim.discard_pile)
				self.game.announce(victim.name_string() + " discards " + str(len(discard_selection)) + " cards")
				victim.update_hand()
				crd.AttackCard.get_next(self, victim)
			else:
				self.played_by.wait("Waiting for other players to discard")
				def post_discard_select_on(discard_selection, victim=victim):
					self.post_discard_select(discard_selection, victim)

				victim.select(2, 2, crd.card_list_to_titles(victim.hand.card_array()), "Discard two cards from hand")
				victim.waiting["on"].append(victim)
				victim.waiting["cb"] = post_discard_select_on


	def post_discard_select(self, selection, victim):
		self.game.announce(victim.name_string() + " discards " + str(len(selection)) + " cards")
		victim.discard(selection, victim.discard_pile)
		victim.update_hand()
		crd.AttackCard.get_next(self, victim)

class Upgrade(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Upgrade"
		self.description = "+1 Card; +1 Action\n Trash a card from your hand. Gain a card costing exactly $1 more than it."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.draw(1)
		self.played_by.update_hand()
		self.game.announce("-- gaining +1 action and drawing a card.")

		selection = self.played_by.hand.auto_select(1, False)
		if selection:
			self.trash_select(selection[0])
		else:
			self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Choose a card to trash:")
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.trash_select

	def trash_select(self, selection):
		card = self.played_by.hand.get_card(selection[0])
		self.played_by.discard([card.title], self.game.trash_pile)
		self.game.announce("-- trashing " + card.log_string() + " to gain a card with cost " + str(card.price + 1))
		self.played_by.update_hand()

		if self.game.supply.pile_contains(card.price + 1):
			self.played_by.select_from_supply(card.price + 1, True)
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select
		else:
			self.game.announce(" however there are no cards with cost " + str(card.price + 1))
			crd.Card.on_finished(self)

	def post_select(self, selection):
		self.played_by.gain(selection)
		crd.Card.on_finished(self)


class Trading_Post(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Trading Post"
		self.description = "Trash 2 cards from your hand.\n If you do, gain a silver card; put it into your hand."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)

		selection = self.played_by.hand.auto_select(2, True)

		if selection:
			self.post_select(selection)
		else:
			self.played_by.select(2, 2, crd.card_list_to_titles(self.played_by.hand.card_array()), "Trash 2 cards from your hand")
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		if len(selection) == 0:
			self.game.announce("But there was nothing to trash")
		else:
			self.game.announce("Trashing " + ", ".join(list(map(lambda x: self.game.log_string_from_title(x), selection))))
			self.played_by.discard(selection, self.game.trash_pile)

		if len(selection) >= 2:
			self.played_by.gain_to_hand("Silver")

		crd.Card.on_finished(self)


# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------

class Harem(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Harem"
		self.description = "$2\n 2 VP"
		self.price = 6
		self.value = 2
		self.vp = 2
		self.type = "Treasure|Victory"

	def log_string(self, plural=False):
		return "".join(["<span class='label label-danger-success'>", self.title + "s</span>" if plural else self.title, "</span>"])

	def get_vp(self):
		return self.vp

class Nobles(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Nobles"
		self.description = "2 VP\n Choose one: +3 Cards, or +2 Actions."
		self.price = 6
		self.vp = 2
		self.type = "Action|Victory"

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
		return "".join(["<span class='label label-default-success'>", "Nobles</span>" if plural else self.title, "</span>"])
