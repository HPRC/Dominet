import sets.card as crd
import tornado.gen as gen

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
		drawn = self.played_by.draw(3)
		self.game.announce("-- drawing " + drawn)
		self.played_by.update_resources()
		self.played_by.update_hand()
		if self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Choose a card to put back on top of your deck."):
			self.played_by.set_cb(self.post_select)
		else:
			crd.Card.on_finished(self, True, False)

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
		self.played_by.set_cb(self.post_select)

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


class Secret_Chamber(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Secret Chamber"
		self.description = "Discard any number of cards. +$1 per card discarded.\n Reaction: When another player plays an Attack card, you may reveal this from your hand. If you do, +2 cards, then put 2 cards from your hand on top of your deck."
		self.price = 2
		self.type = "Action|Reaction"
		self.trigger = "Attack"
		self.reacted_to_callback = None

	def play(self, skip=False):
		crd.Card.play(self, skip)

		self.played_by.select(None, None,
		                      crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to discard")
		self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.balance += len(selection)
		self.game.announce(self.played_by.name_string() + " discarding " + str(len(selection)) + " gaining +$" + str(len(selection)) + ".")
		crd.Card.on_finished(self)

	# below is reaction code
	def react(self, reacted_to_callback):
		self.reacted_to_callback = reacted_to_callback
		self.played_by.select(1, 1, ["Reveal", "Hide"],
		                      "Reveal " + self.title + " to draw 2 and place 2 back to deck?")

		self.played_by.set_cb(self.post_reveal, True)

	def post_reveal(self, selection):
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			drawn_cards = self.played_by.draw(2, False)
			self.played_by.update_hand()
	
			def post_react_draw_select_cb(selected, drawn_cards=drawn_cards):
				self.post_react_draw_select(selected, drawn_cards)

			if self.played_by.select(2, 2, crd.card_list_to_titles(self.played_by.hand.card_array()), 
				"Put two cards to the top of your deck (#1 is on top)", True):
				self.played_by.set_cb(post_react_draw_select_cb, True)
			else:
				#temp to clear our reacted callback before calling it
				temp = self.reacted_to_callback
				self.reacted_to_callback = None
				temp()
		else:
			#temp to clear our reacted callback before calling it
			temp = self.reacted_to_callback
			self.reacted_to_callback = None
			temp()

	def post_react_draw_select(self, selection, drawn_cards):
		self.played_by.discard(selection, self.played_by.deck)
		self.game.announce("-- drawing two cards, putting two of them on the top of their deck.")
		self.played_by.update_hand()
		#if we put back the drawn card then remove from drawn list
		final_drawn = [x for x in drawn_cards if x != self.played_by.deck[-1] and x!= self.played_by.deck[-2]]
		#temp to clear our reacted callback before calling it
		#pass in newly drawn cards to check for new reactions
		temp = self.reacted_to_callback
		self.reacted_to_callback = None
		temp(final_drawn)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])


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


class Masquerade(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Masquerade"
		self.description = "+2 Cards\n Each player passes a card in their hand to the player on their left. You may trash a card from your hand."
		self.price = 3
		self.type = "Action"
		self.passed_card = ""

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.draw(2)
		self.played_by.update_hand()
		self.fire(self.played_by)

	# custom get_next since masquerade is not an attack card
	def get_next(self, player):
		next_player_index = (self.game.players.index(player) + 1) % len(self.game.players)
		if self.game.players[next_player_index] != self.played_by:
			self.fire(self.game.players[next_player_index])
		else:
			self.played_by.select(None, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Select a card to trash")
			self.played_by.set_cb(self.trash_select)

	def fire(self, player):
		def post_fire(selection, player=player):
			self.post_select(selection, player)

		# need to know which card was passed to them so we can know which card to NOT show user and remove from card_array()
		card = player.hand.extract(self.passed_card)
		player.select(1, 1, crd.card_list_to_titles(player.hand.card_array()), "Select a card to pass to player on your left")
		if card is not None:
			player.hand.add(card)

		player.set_cb(post_fire)

	def post_select(self, selection, player):
		left_opponent = player.get_left_opponent()
		player.announce_self("-- you pass " + self.game.log_string_from_title(selection[0]))
		# logging what we received after we pass our card
		if self.passed_card != "":
			player.announce_self("-- you received " + self.game.log_string_from_title(self.passed_card))
		else:
			# we are the first player, wait for everyone
			self.played_by.wait_many("to pass", self.played_by.get_opponents())
		self.passed_card = selection[0]
		card = player.hand.extract(selection[0])
		card.played_by = left_opponent
		left_opponent.hand.add(card)
		player.update_hand()

		# if we are last, update the first person's receive log
		if left_opponent == self.played_by:
			self.played_by.announce_self("-- you received " + self.game.log_string_from_title(selection[0]))
			self.played_by.update_hand()

		self.get_next(player)

	def trash_select(self, selection):
		if len(selection) > 0:
			self.game.announce("-- " + self.played_by.name_string() + " trashes " + self.played_by.hand.get_card(selection[0]).log_string())
			self.played_by.discard([selection[0]], self.game.trash_pile)
		self.passed_card = ""
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
			drawn = self.played_by.draw(2)
			self.game.announce("-- drawing " + drawn)

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
		self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		if "+$2" in selection:
			self.played_by.balance += 2
			self.game.announce("-- gaining +$2")
			crd.Card.on_finished(self, False)

		elif "+2 Cards" in selection:
			drawn = self.played_by.draw(2)
			self.game.announce("-- drawing " + drawn)
			crd.Card.on_finished(self)
		elif "Trash 2 cards from hand" in selection:
			self.game.announce("-- choosing to trash 2 cards from hand")

			if len(self.played_by.hand) > 2 and not self.played_by.hand.is_homogeneous():
				self.played_by.select(2, 2, crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to trash")
				self.played_by.set_cb(self.trash_select)
			else:
				card_selection = self.played_by.hand.auto_select(2, True)
				self.trash_select(card_selection)

	def trash_select(self, selection):
		if len(selection) == 0:
			selection_string = "nothing"
		else:
			selection_string = ", ".join(list(map(lambda x: self.game.log_string_from_title(x), selection)))
		self.game.announce(self.played_by.name_string() + " trashes " + selection_string)
		self.played_by.discard(selection, self.game.trash_pile)
		crd.Card.on_finished(self, True, False)


class Swindler(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Swindler"
		self.description = "+$2\n Each other player trashes the top card of their deck and gains a card with the same cost that you choose."
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
			if topdeck is not None:
				player.update_deck_size()
				player.game.trash_pile.append(topdeck)
				player.game.update_trash_pile()
				self.game.announce(self.played_by.name_string() + " trashes " + self.game.log_string_from_title(topdeck.title)
				                   + " from the top of " + player.name_string() + "'s deck.")

				def post_select_on(selection, player=player):
					self.post_select(selection, player)

				if self.played_by.select_from_supply(topdeck.get_price(), True):
					self.played_by.set_cb(post_select_on)
				else:
					crd.AttackCard.get_next(self, player)
			else:
				self.game.announce(player.name_string() + " has no cards to Swindle.")
				crd.AttackCard.get_next(self, player)

	def post_select(self, selection, victim):
		victim.gain(selection[0], done_gaining= lambda : crd.AttackCard.get_next(self, victim))

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
		self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		topdeck = self.played_by.topdeck()
		self.game.announce("-- wishing for a " + self.game.log_string_from_title(selection[0]))
		if topdeck:
			if topdeck.title == selection[0]:
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
			self.played_by.set_cb(self.post_select)

		else:
			self.played_by.gain("Estate", done_gaining=lambda : crd.Card.on_finished(self, False))

	def post_select(self, selection):
		if "Yes" in selection:
			self.played_by.balance += 4
			self.game.announce("-- discarding an " + self.played_by.hand.data['Estate'][0].log_string() + " and gaining +$4 ")
			self.played_by.discard(["Estate"], self.played_by.discard_pile)
		else:
			self.played_by.gain("Estate", done_gaining=lambda : crd.Card.on_finished(self))
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
		for i in self.game.supply.unique_cards():
			self.game.price_modifier[i.title] -= 1
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

		announcement = "-- gaining $2"
		if self.played_by.played_actions >= 3:
			self.played_by.actions += 1
			drawn = self.played_by.draw(1)
			announcement += " and drawing " + drawn + " and gaining +1 action"
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
				card.value = 1

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

		if self.played_by.select_from_supply(4):
			self.played_by.set_cb(self.post_select)
		else:
			crd.Card.on_finished(self, False, False)

	def post_select(self, selection):
		card = self.game.card_from_title(selection[0])
		
		def post_gain(card= card):
			effects = []
			if "Action" in card.type:
				self.played_by.actions += 1
				effects.append("gaining 1 action")
			if "Treasure" in card.type:
				self.played_by.balance += 1
				effects.append("gaining +$1")
			if "Victory" in card.type:
				drawn = self.played_by.draw(1)
				effects.append("drawing " + drawn)
			if not card.type == "Curse":
				self.game.announce("-- " + " and ".join(effects))
			crd.Card.on_finished(self)

		self.played_by.gain(selection[0], True, done_gaining=lambda : post_gain())


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
		self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		if "Yes" in selection:
			if len(self.game.trash_pile) > 0 and self.game.trash_pile[-1] == self:
				self.game.announce("-- tries to trash " + self.log_string() + " but it was already trashed")
			elif self in self.played_by.played:
				self.game.announce("-- trashing " + self.log_string() + " to gain $2")
				self.played_by.balance += 2
				self.played_by.played.pop()
				self.game.trash_pile.append(self)
				self.game.update_trash_pile()
		crd.Card.on_finished(self)

class Scout(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Scout"
		self.description = "+1 Action \n Reveal the top 4 cards of your deck and draw any Victory cards, put the other cards on top of your deck in any order."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.update_resources()
		if len(self.played_by.deck) < 4:
			self.played_by.shuffle_discard_to_deck()

		revealed = []
		if len(self.played_by.deck) < 4:
			revealed = self.played_by.deck
		else:
			revealed = self.played_by.deck[-4:]
		# removed the revealed cards from deck
		num_truncate = len(revealed)
		del self.played_by.deck[-num_truncate:]
		if len(revealed) != 0:
			self.game.announce("-- revealing " + ", ".join(list(map(lambda x: x.log_string(), revealed))))
		else:
			self.game.announce("-- revealing nothing")
		victory_cards = [x for x in revealed if "Victory" in x.type]
		if len(victory_cards) > 0:
			victory_card_titles = [x.log_string() for x in victory_cards]
			self.game.announce("-- putting " + ", ".join(victory_card_titles) + " into their hand")
		for vc in victory_cards:
			self.played_by.hand.add(vc)
		self.played_by.update_hand()
		self.played_by.update_deck_size()

		cards_left = [x for x in revealed if "Victory" not in x.type]
		crd.reorder_top(self.played_by, cards_left, lambda : crd.Card.on_finished(self, False, False))

# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------


class Duke(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Duke"
		self.description = "Worth 1 VP for each Duchy you have."
		self.price = 5
		self.vp = 0
		self.type = "Victory"

	def get_vp(self):
		hand_count = self.played_by.hand.get_count('Duchy')
		deck_count = self.played_by.get_card_count_in_list('Duchy', self.played_by.deck)
		discard_count = self.played_by.get_card_count_in_list('Duchy', self.played_by.discard_pile)
		return int(hand_count + deck_count + discard_count)


class Minion(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Minion"
		self.description = "+1 Action\n Choose one: +$2 or discard your hand, draw 4 cards and each other player\
		with at least 5 cards in hand discards their hand and draws 4 cards."
		self.price = 5
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.update_resources()
		self.game.announce("-- gaining 1 action")
		self.played_by.select(1, 1, ["+$2", "discard hand and draw 4 cards"], "Choose one:")
		self.played_by.set_cb(self.post_selection)

	def post_selection(self, selection):
		if "+$2" in selection[0]:
			self.played_by.balance += 2
			self.game.announce("-- gaining $2")
			crd.Card.on_finished(self, False, True)
		else:
			self.played_by.discard(crd.card_list_to_titles(self.played_by.hand.card_array()), self.played_by.discard_pile)
			drawn = self.played_by.draw(4)
			self.game.announce("-- drawing " + drawn)
			self.played_by.update_hand()
			crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		for i in self.played_by.get_opponents():
			if not crd.AttackCard.is_blocked(self, i):
				if len(i.hand) >= 5:
					self.game.announce("-- " + i.name_string() + " discards hand and draws 4")
					i.discard(crd.card_list_to_titles(i.hand.card_array()), i.discard_pile)
					i.draw(4)
					i.update_hand()
				else:
					self.game.announce("-- " + i.name_string() + " has less than 5 cards in hand")
		crd.Card.on_finished(self, False, False)


class Torturer(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Torturer"
		self.description = "+3 Cards\n Each other player chooses one: he discards 2 cards; or he gains a Curse card, putting it in their hand."
		self.price = 5
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(3)
		self.played_by.update_hand()
		self.played_by.update_resources()
		self.game.announce("-- drawing " + drawn)
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		crd.AttackCard.get_next(self, self.played_by)

	@gen.coroutine
	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			player.select(1, 1, ["Discard 2 cards", "Gain a Curse"], "Choose one:")
			player.opponents_wait("to choose", True)
			selection = yield player.set_cb()
			if selection[0] == 'Gain a Curse':
				player.update_wait(True)
				player.gain_to_hand('Curse', done_gaining= lambda : crd.AttackCard.get_next(self, player))
			else:
				discard_selection = player.hand.auto_select(2, True)
				if discard_selection:
					player.discard(discard_selection, player.discard_pile)
					self.game.announce(player.name_string() + " discards " + str(len(discard_selection)) + " cards")
					player.update_hand()
					crd.AttackCard.get_next(self, player)
				elif len(player.hand) == 0:
					crd.AttackCard.get_next(self, player)
				else:
					player.opponents_wait("to discard", locked=False)

					def post_discard_select_on(discard_selection, player=player):
						self.post_discard_select(discard_selection, player)

					player.select(2, 2, crd.card_list_to_titles(player.hand.card_array()), "Discard two cards from hand")
					discard_selection = yield player.set_cb()
					self.game.announce(player.name_string() + " discards " + str(len(discard_selection)) + " cards")
					player.discard(discard_selection, player.discard_pile)
					player.update_hand()
					player.update_wait(True)
					crd.AttackCard.get_next(self, player)


class Tribute(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Tribute"
		self.description = "The player to your left reveals then discards the top 2 cards of their deck.\n" \
		                   " For each differently named card revealed, if it is an… Action Card; +2 Actions;" \
		                   " Treasure Card; +$2; Victory Card; +2 Cards."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)

		tributes = list()
		left_opponent = self.played_by.get_left_opponent()

		topdeck1 = left_opponent.topdeck()
		topdeck2 = left_opponent.topdeck()
		left_opponent.discard_pile.append(topdeck1)
		left_opponent.discard_pile.append(topdeck2)
		left_opponent.update_deck_size()
		left_opponent.update_discard_size()
		tributes.append(topdeck1)
		if topdeck1.title != topdeck2.title:
			tributes.append(topdeck2)
		self.game.announce("-- "+ left_opponent.name_string() + " reveals " + ", ".join(crd.card_list_log_strings([topdeck1, topdeck2])) + " as a tribute.")

		self.tribute_card(left_opponent, tributes)

	def tribute_card(self, left_opponent, tributes):
		for x in tributes:
			gaining = []
			if "Action" in x.type:
				self.played_by.actions += 2
				gaining.append("gaining 2 actions")
			if "Treasure" in x.type:
				self.played_by.balance += 2
				gaining.append("gaining +$2")
			if "Victory" in x.type:
				drawn = self.played_by.draw(2)
				gaining.append("drawing " + drawn)
			if "Curse" != x.type:
				self.game.announce("-- " + " and ".join(gaining) + " for " + x.log_string())
		crd.Card.on_finished(self)


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
			self.trash_select(selection)
		else:
			if self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), 
				"Choose a card to trash:"):
				self.played_by.set_cb(self.trash_select)
			else:
				crd.Card.on_finished(self)

	def trash_select(self, selection):
		card = self.played_by.hand.get_card(selection[0])
		self.played_by.discard([card.title], self.game.trash_pile)
		self.game.announce("-- trashing " + card.log_string() + " to gain a card with cost " + str(card.get_price() + 1))
		self.played_by.update_hand()

		if self.played_by.select_from_supply(card.get_price() + 1, True):
			self.played_by.set_cb(self.post_select)
		else:
			crd.Card.on_finished(self)

	def post_select(self, selection):
		self.played_by.gain(selection[0], done_gaining=lambda : crd.Card.on_finished(self))

class Saboteur(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Saboteur"
		self.description = "Each other player reveals cards from the top of their deck until revealing one costing $3 or more.\n" \
		                   "He trashes that card and may gain a card costing at most $2 less than it.\n" \
		                   "He discards the other revealed cards."
		self.price = 5
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		crd.AttackCard.get_next(self, self.played_by)

	def fire(self, victim):
		# check if blocked by moat first.
		if not crd.AttackCard.fire(self, victim):
			return

		self.game.announce("-- " + victim.name_string() + " is being sabotaged")

		sabotaged = False
		crd.search_deck_for(victim, lambda x : x.price >=3, lambda c: self.found(c, victim=victim))

	def found(self, card, victim):
		if card is None:
			self.game.announce("-- but there was nothing to sabotage")
			crd.AttackCard.get_next(self, victim)
		else:
			self.game.trash_pile.append(card)
			self.game.update_trash_pile()
			self.game.announce("-- trashing " + card.log_string())

			def post_select_cb(selection, victim=victim):
				self.post_select(selection, victim)

			self.game.announce("-- " + victim.name_string() + " gains a card costing "
			                   + str(card.get_price() - 2) + " or less")
			victim.select_from_supply(price_limit=card.get_price() - 2, optional=True)
			victim.set_cb(post_select_cb)
			self.played_by.wait("to gain a card", victim)

	def post_select(self, selection, victim):
		if selection[0] != "None":
			victim.gain(selection[0], done_gaining=lambda : crd.AttackCard.get_next(self, victim))
		else:
			self.game.announce("-- " + victim.name_string() + " gains nothing")
			crd.AttackCard.get_next(self, victim)
		


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
			self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		if len(selection) == 0:
			self.game.announce("But there was nothing to trash")
		else:
			self.game.announce("Trashing " + ", ".join(list(map(lambda x: self.game.log_string_from_title(x), selection))))
			self.played_by.discard(selection, self.game.trash_pile)

		if len(selection) >= 2:
			self.played_by.gain_to_hand("Silver", done_gaining=lambda : crd.Card.on_finished(self))
		else:
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
		self.played_by.set_cb(self.post_select)

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
