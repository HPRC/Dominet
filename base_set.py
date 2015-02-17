import card as crd


# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------

class Cellar(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Cellar"
		self.description = "+1 action\n Discard any number of cards, +1 Card per card discarded."
		self.price = 2
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.select(None, None,
			crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to discard")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		self.played_by.write_json(command="announce", msg="-- you discard " + 
			" , ".join(list(map(lambda x: self.game.card_from_title(x).log_string(), selection))))
		self.played_by.announce_opponents("-- discarding and drawing " + str(len(selection)) + " cards")
		self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.draw(len(selection))
		crd.Card.on_finished(self)


class Chapel(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Chapel"
		self.description = "Trash up to 4 cards from your hand."
		self.price = 2
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(None, 4,
			crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to trash")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		selection_string = list(map(lambda x: self.game.card_from_title(x).log_string(), selection))
		if len(selection_string) > 0:
			self.game.announce(self.played_by.name_string() + " trashes " + ", ".join(selection_string));
		else:
			self.game.announce(self.played_by.name_string() + " trashes nothing");
		self.played_by.waiting["cb"] = None
		self.played_by.discard(selection, self.game.trash_pile)
		crd.Card.on_finished(self)


class Moat(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Moat"
		self.description = "+2 cards\n Whenever another player plays an Attack card, you may reveal this card from your hand, if you do, you are unaffected by the Attack."
		self.price = 2
		self.type = "Action|Reaction"
		self.trigger = "Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.game.announce(" -- drawing " + drawn)
		crd.Card.on_finished(self)

	def react(self, react_to_callback):
		self.played_by.select(1, 1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to prevent attack?")

		def new_cb(selection):
			self.post_select(selection)
			react_to_callback()

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = new_cb

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			self.played_by.protection += 1

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])


# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

class Village(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Village"
		self.description = "+1 card\n +2 actions"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining 2 actions and drawing " + drawn)
		crd.Card.on_finished(self)


class Chancellor(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Chancellor"
		self.description = "+$2\nYou may immediately put your deck into your discard pile"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.select(1, 1, ["Yes", "No"],  
			"Put discard into deck?")
		self.played_by.waiting["cb"] = self.post_select
		self.played_by.waiting["on"].append(self.played_by)

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		if selection[0] == "Yes":
			self.played_by.shuffle_discard_to_deck()
		crd.Card.on_finished(self)


class Woodcutter(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Woodcutter"
		self.description = "$2\n +1 Buy"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining $2 and 1 buy")
		crd.Card.on_finished(self)


class Workshop(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Workshop"
		self.description = "Gain a card costing up to $4"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.select_from_supply(4, False)

	def post_gain(self, card_title):
		self.played_by.gain(card_title)
		crd.Card.on_finished(self, False, False)


# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------

class Bureaucrat(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Bureaucrat"
		self.description = "Gain a Silver, put it on top of your deck. Each other player reveals a Victory card\
		and puts it on his deck or reveals a hand with no Victory cards."
		self.price = 4

	def play(self, skip=False):
		crd.Card.play(self, skip)
		# create silver and add to top of deck
		silver = crd.Silver(self.game, self.played_by)
		self.game.announce(" -- gaining a " + silver.log_string())
		self.played_by.deck.append(silver)		
		self.played_by.update_resources()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		for i in self.played_by.get_opponents():
			if not crd.AttackCard.is_blocked(self, i):
				i_victory_cards = set(i.hand.get_cards_by_type("Victory"))
				if len(i_victory_cards) == 0:
					self.game.announce(i.name_string() + " has no Victory cards & reveals " + i.hand.reveal_string())
					crd.Card.on_finished(self, False, False)
				elif len(i_victory_cards) == 1:
					self.game.announce(i.name_string() + " puts " + i_victory_cards[0].log_string() + " back on top of the deck")
					i.discard([i_victory_cards[0].title], i.deck)
					i.update_hand()
					crd.Card.on_finished(self, False, False)
				else:
					i.select(1, 1, crd.card_list_to_titles(i_victory_cards),
						"select Victory card to put back")

					def post_select_on(selection, i=i):
						self.post_select(selection, i)

					i.waiting["on"].append(i)
					i.waiting["cb"] = post_select_on
					self.played_by.waiting["on"].append(i)
					self.played_by.wait("Waiting for other players to choose a Victory card to put back")

	def post_select(self, selection, victim):
		victim.discard(selection, victim.deck)
		self.game.announce(victim.name_string() + " puts " + self.game.card_from_title(selection[0]).log_string() + " back on top of the deck")
		victim.update_hand()
		crd.Card.on_finished(self, False, False)


class Feast(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Feast"
		self.type = "Action"
		self.description = "Trash this card, gain a card costing up to $5."
		self.price = 4

	def play(self, skip=False):
		crd.Card.play(self, skip)
		if self.played_by.played[-1] == self:
			self.game.trash_pile.append(self.played_by.played.pop())
			self.game.update_trash_pile()
			self.game.announce("-- trashing " + self.log_string())
		self.played_by.update_resources()
		self.played_by.select_from_supply(5, False)
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain

	def post_gain(self, card_title):
		self.played_by.gain(card_title)
		crd.Card.on_finished(self, False, False)


class Gardens(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Gardens"
		self.description = "+1 VP for every 10 cards in your deck (rounded down)"
		self.price = 4
		self.vp = 0

	def get_vp(self):
		return int(self.played_by.total_deck_size()/10)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", self.title, "</span>"])


class Militia(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Militia"
		self.description = "+$2\n Each other player discards down to 3 cards in hand."
		self.price = 4
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.update_resources()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		for i in self.played_by.get_opponents():
			if not crd.AttackCard.is_blocked(self, i):
				if len(i.hand) > 3:
					i.select(len(i.hand) - 3, len(i.hand) - 3, crd.card_list_to_titles(i.hand.card_array()),
						"discard down to 3 cards")

					def post_select_on(selection, i=i):
						self.post_select(selection, i)

					i.waiting["on"].append(i)
					i.waiting["cb"] = post_select_on
					self.played_by.waiting["on"].append(i)
					self.played_by.wait("Waiting for other players to discard")
				else:
					self.game.announce("-- " + i.name_string() + " has 3 cards in hand")

	def post_select(self, selection, victim):
		self.game.announce("-- " + victim.name_string() + " discards down to 3")
		victim.discard(selection, victim.discard_pile)
		victim.update_hand()
		if len(self.played_by.waiting["on"]) == 0:
			crd.Card.on_finished(self, False, False)


class Moneylender(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Moneylender"
		self.description = "trash a copper from your hand, if you do +$3"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		if "Copper" in self.played_by.hand:
			self.played_by.discard(["Copper"], self.game.trash_pile)
			self.played_by.balance += 3
			self.game.announce("-- trashing a " + self.game.log_string_from_title("Copper") + " and gaining $3")
		else:
			self.game.announce("-- but has no " + self.game.log_string_from_title("Copper") + " to trash")
		crd.Card.on_finished(self)


class Remodel(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Remodel"
		self.description = "Trash a card from your hand, gain a card costing up to 2 more than the trashed card"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		 "select card to remodel")
		self.played_by.update_resources()
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.discard(selection, self.game.trash_pile)
		card_trashed = self.game.card_from_title(selection[0])
		self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
		self.played_by.select_from_supply(card_trashed.price + 2, False)

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.update_hand()

	def post_gain(self, card_title):
		self.played_by.gain(card_title)
		crd.Card.on_finished(self, False, False)


class Spy(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Spy"
		self.description = "+1 card\n +1 action\n Each player (including you) reveals the top card of his deck and either discards it or puts it back, your choice"
		self.price = 4

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- getting +1 action and drawing " + drawn)
		self.played_by.update_resources()
		self.played_by.update_hand()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		self.fire(self.played_by)

	def fire(self, player):
		if not crd.AttackCard.is_blocked(self, player):
			if len(player.deck) < 1:
				player.shuffle_discard_to_deck()
				if len(player.deck) < 1:
					self.game.announce(player.name_string() + " has no cards to Spy.")
					self.get_next(player)
					return
			revealed_card = player.deck[-1]
			self.played_by.select(1, 1, ["discard", "keep"],  
				player.name + " revealed " + revealed_card.title)

			def post_select_on(selection, player=player):
				self.post_select(selection, player)

			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = post_select_on
		else:
			self.get_next(player)

	def post_select(self, selection, victim):
		if selection[0] == "discard":
			card = victim.deck.pop()
			victim.discard_pile.append(card)
			self.played_by.update_deck_size()
			self.played_by.update_discard_size()
			self.game.announce(self.played_by.name_string() + " discards " + card.log_string() + " from " +
				victim.name_string() + "'s deck")
		else:
			card = victim.deck[-1]
			self.game.announce(self.played_by.name_string() + " leaves " + card.log_string() + " on " +
				victim.name_string() + "'s deck")
		self.get_next(victim)

	def get_next(self, victim):
		next_player_index = (self.game.players.index(victim) + 1) % len(self.game.players)
		if self.game.players[next_player_index] != self.played_by:
			self.fire(self.game.players[next_player_index])
		else:
			crd.Card.on_finished(self, False, False)


class Smithy(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Smithy"
		self.description = "+3 cards"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(3)
		self.game.announce("-- drawing " + drawn)
		crd.Card.on_finished(self)


class Thief(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Thief"
		self.description = "Each other player reveals and discards the top 2 cards of his deck. If they revealed any Treasure cards, they trash one that you choose and you may gain the trashed card."
		self.price = 4

	def play(self, skip=False):
		crd.Card.play(self, skip)
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		self.get_next(self.played_by)

	def fire(self, player):
		if not crd.AttackCard.is_blocked(self, player):
			if len(player.deck) < 2:
				player.shuffle_discard_to_deck()
				if len(player.deck) < 2:
					self.game.announce(player.name_string() + " has no cards to Thieve.")
					self.get_next(player)
					return
			revealed_cards = [player.deck.pop(), player.deck.pop()]
			revealed_treasure = [x for x in revealed_cards if "Treasure" in x.type]
			self.game.announce(player.name_string() + " revealed "
				+ ", ".join([x.log_string() for x in revealed_cards]))
			if len(revealed_treasure) > 0:
				if len(revealed_treasure) == 1 or revealed_treasure[0].title == revealed_treasure[1].title:
					self.game.trash_pile.append(revealed_treasure[0])
					self.game.update_trash_pile()
					if revealed_cards[0] == revealed_treasure[0]:
						player.discard_pile.append(revealed_cards[1])
					else:
						player.discard_pile.append(revealed_cards[0])
					self.game.announce(player.name_string() + " trashes "
					+ revealed_treasure[0].log_string())

					self.played_by.select(1, 1, ["Yes", "No"],
						"Gain " + revealed_treasure[0].title + "?")

					def post_select_gain(selection, thieved=player, card=revealed_treasure[0].title):
						self.post_select_gain(selection, thieved, card)

					self.played_by.waiting["on"].append(self.played_by)
					self.played_by.waiting["cb"] = post_select_gain
				else:
					self.played_by.select(1, 1, crd.card_list_to_titles(revealed_treasure),
						"Choose" + player.name + "'s Treasure to trash")

					def post_select_trash(selection, thieved=player, cards=revealed_treasure):
						self.post_select_trash(selection, thieved, cards)

					self.played_by.waiting["on"].append(self.played_by)
					self.played_by.waiting["cb"] = post_select_trash
			else:
				crd.Card.on_finished(self, True, True)
		else:
			self.get_next(player)

	def post_select_gain(self, selection, thieved, card):
		if selection[0] == "Yes":
			self.game.trash_pile.pop()
			self.played_by.gain(card, False)
		self.get_next(thieved)

	def post_select_trash(self, selection, thieved, cards):
		card_to_trash = [x for x in cards if selection[0] == x.title][0]
		cards.remove(card_to_trash)
		self.game.trash_pile.append(card_to_trash)
		self.game.update_trash_pile()
		thieved.discard_pile.append(cards[0])
		self.game.announce(self.played_by.name_string() + " trashes " + card_to_trash.log_string() + " from " +
				thieved.name_string() + "'s deck")
		self.game.announce(thieved.name_string() + " discards " + cards[0].log_string() + " from his deck")
		self.played_by.select(1, 1, ["Yes", "No"], "Gain " + card_to_trash.title + "?")

		def post_select_gain(selection, thieved=thieved, card=card_to_trash.title):
			self.post_select_gain(selection, thieved, card)

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = post_select_gain

	def get_next(self, victim):
		next_player_index = (self.game.players.index(victim) + 1) % len(self.game.players)
		if self.game.players[next_player_index] != self.played_by:
			self.fire(self.game.players[next_player_index])
		else:
			crd.Card.on_finished(self, True, True)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-danger'>", "Thieves" if plural else self.title, "</span>"])


class Throne_Room(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Throne Room"
		self.description = "Choose an action card from your hand. Play it twice."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		action_cards = self.played_by.hand.get_cards_by_type("Action")
		if not self.played_by.select(1, 1, crd.card_list_to_titles(action_cards),
		 "select card for Throne Room"):
			self.done = lambda : None
			self.game.announce(" -- but has no action cards")
		else:
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select
		self.played_by.update_resources()

	def post_select(self, selection):
		selected_card = self.played_by.hand.get_card(selection[0])
		throne_room_str = self.played_by.name_string() + " " + self.log_string(True) + " " + selected_card.log_string()
		def second_play(card=selected_card):

			def final_done(card=card):
				# after the second play of card is finished, throne room is done
				card.done = lambda: None
				crd.Card.on_finished(self, False, False)

			card.game.announce(throne_room_str)
			card.done = final_done
			card.play(True)
			card.played_by.update_resources()
		selected_card.done = second_play
		self.played_by.discard(selection, self.played_by.played)
		self.game.announce(throne_room_str)
		selected_card.play(True)
		self.played_by.update_resources()
		self.played_by.update_hand()


# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Council_Room(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Council Room"
		self.description = "+4 cards\n +1 buy\n Each other player draws a card"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(4)
		self.played_by.buys += 1
		self.game.announce("-- drawing " + drawn + " and getting +1 buy")
		self.game.announce("-- each other player draws a card")
		for i in self.game.players:
			if i != self.played_by:
				i.draw(1)
				i.update_hand()
		crd.Card.on_finished(self)


class Festival(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Festival"
		self.description = "+$2\n +2 actions\n +1 buy"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.actions += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining 2 actions, 1 buy and $2")
		crd.Card.on_finished(self, False)


class Laboratory(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Laboratory"
		self.description = "+2 cards\n +1 action"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.played_by.actions += 1
		self.game.announce("-- drawing " + drawn + " and gaining +1 action")
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", "Laboratories" if plural else self.title, "</span>"])


class Library(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Library"
		self.description = "Draw until you have 7 cards in hand. You may set aside any action cards drawn this way. Discard the set aside cards after drawing"
		self.price = 5
		self.type = "Action"
		self.set_aside = []

	def play(self, skip=False):
		crd.Card.play(self, skip)
		while len(self.played_by.hand) < 7:
			top_card = self.played_by.topdeck()
			if top_card != None:
				if "Action" in top_card.type:
					self.played_by.select(1, 1, ["Yes", "No"], "set aside " + top_card.title + "?")

					def post_select_card(selection, card=top_card):
						self.post_select(selection, card)

					self.played_by.waiting["cb"] = post_select_card
					self.played_by.waiting["on"].append(self)
					return
				else:
					self.played_by.write_json(command="announce",msg="-- You draw " + top_card.log_string())
					self.played_by.announce_opponents(msg="-- drawing 1 card")
					self.played_by.hand.add(top_card)
					self.played_by.update_hand()
			else:
				self.played_by.write_json(command="announce",msg="-- You have no cards left to draw")
				break
		self.on_finish()

	def post_select(self, selection, card):
		self.played_by.waiting["cb"] = None
		if selection[0] == "No":
			self.played_by.write_json(command="announce", msg="-- You draw " + card.log_string())
			self.played_by.hand.add(card)
			self.played_by.update_hand()
		else:
			self.played_by.write_json(command="announce", msg="-- You set aside " + card.log_string())
			self.set_aside.append(card)
		self.played_by.update_deck_size()
		self.played_by.update_discard_size()
		if len(self.played_by.hand) < 7:
			self.play(True)
		else:
			self.on_finish()

	def on_finish(self):
		self.played_by.discard_pile += self.set_aside
		self.set_aside = []
		self.played_by.update_deck_size()
		self.played_by.update_discard_size()
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", "Libraries" if plural else self.title, "</span>"])


class Market(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Market"
		self.description = "+1 card\n+1 action\n+1 buy\n+$1"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(1)
		self.played_by.actions += 1
		self.played_by.balance += 1
		self.played_by.buys += 1
		self.game.announce("-- drawing " + drawn + " and gaining +1 action")
		crd.Card.on_finished(self)


class Mine(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Mine"
		self.description = "Trash a Treasure card from your hand. Gain a Treasure card costing up to $3 more;\
		put it into your hand."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		treasure_cards = self.hand.get_cards_by_type("Treasure")
		self.played_by.select(1, 1, crd.card_list_to_titles(treasure_cards),
		 "select treasure to trash")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.discard(selection, self.game.trash_pile)
		card_trashed = self.game.card_from_title(selection[0])
		self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.select_from_supply(card_trashed.price + 3, False, "Treasure")

	def post_gain(self, card_title):
		self.played_by.gain(card_title)
		gained_card = self.played_by.discard_pile.pop()
		self.played_by.hand.add(gained_card)
		crd.Card.on_finished(self)


class Witch(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Witch"
		self.description = "+2 cards\n Each other player gains a curse card"
		self.price = 5

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.game.announce("-- drawing " + drawn)
		self.played_by.update_hand()
		self.played_by.update_resources()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		for i in self.played_by.get_opponents():
			if not crd.AttackCard.is_blocked(self, i):
				i.gain("Curse")
		crd.Card.on_finished(self, False, False)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-danger'>", self.title, "es</span>" if plural else "</span>"])


# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------

class Adventurer(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Adventurer"
		self.description = "Reveal cards from your deck until you reveal 2 Treasure cards, put those in your hand and discard the other revealed cards."
		self.price = 6
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		to_discard = []
		treasures = []
		while len(self.played_by.deck) > 0:
			card = self.played_by.deck.pop()
			if "Treasure" in card.type:
				treasures.append(card)
				if len(treasures) == 2:
					self.game.announce(self.played_by.name_string() + " reveals " + " , ".join(crd.card_list_log_strings(to_discard + treasures)))
					self.game.announce(self.played_by.name_string() + " puts " + " , ".join(crd.card_list_log_strings(treasures)) + "in hand")
					self.played_by.discard_pile += to_discard
					self.played_by.update_discard_size()
					self.played_by.update_deck_size()
					for t in treasures:
						self.played_by.hand.add(t)
					crd.Card.on_finished(self)
					return
			else:
				to_discard.append(card)
			if len(treasures) < 2 and len(self.played_by.deck) == 0:
				self.played_by.shuffle_discard_to_deck()

		self.game.announce(self.played_by.name_string() + " reveals " + " , ".join(crd.card_list_log_strings(to_discard + treasures)))
		if len(treasures) > 0:
			self.game.announce(self.played_by.name_string() + " puts " + " , ".join(crd.card_list_log_strings(treasures)) + " in hand")
		else:
			self.game.announce(self.played_by.name_string() + " finds no treasures to put in hand")
		self.played_by.discard_pile += to_discard
		self.played_by.update_discard_size()
		self.played_by.update_deck_size()
		for t in treasures:
			self.played_by.hand.add(t)
		crd.Card.on_finished(self)

