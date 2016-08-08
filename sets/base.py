import sets.card as crd
import tornado.gen as gen
import sets.supply as supply


# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------

class Cellar(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Cellar"
		self.description = "{}Discard any number of cards, +1 Card per card discarded.".format(crd.format_actions(1))
		self.price = 2
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		selection = yield self.played_by.select(None, None,
			crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to discard")
		if len(selection) > 0:
			self.played_by.announce_self("-- you discard " + 
				" , ".join(list(map(lambda x: self.game.card_from_title(x).log_string(), selection))))
		else:
			self.played_by.announce_self("-- you discard nothing")
		self.played_by.announce_opponents("-- discarding and drawing " + str(len(selection)) + " cards")
		yield self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.draw(len(selection))
		crd.Card.on_finished(self)


class Chapel(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Chapel"
		self.description = "Trash up to 4 cards from your hand."
		self.price = 2
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		selection = yield self.played_by.select(None, 4,
			crd.card_list_to_titles(self.played_by.hand.card_array()), "select cards to trash")
		selection_string = list(map(lambda x: self.game.card_from_title(x).log_string(), selection))
		if len(selection_string) > 0:
			self.game.announce(self.played_by.name_string() + " trashes " + ", ".join(selection_string))
		else:
			self.game.announce(self.played_by.name_string() + " trashes nothing")
		yield self.played_by.discard(selection, self.game.trash_pile)
		crd.Card.on_finished(self, True, False, False)

class Moat(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Moat"
		self.description = "{} Reaction: Whenever another player plays an Attack card,\
		                   you may reveal this card from your hand,\
		                   if you do, you are unaffected by the Attack.".format(crd.format_draw(2))
		self.price = 2
		self.type = "Action|Reaction"
		self.trigger = "Attack"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.game.announce(" -- drawing " + drawn)
		crd.Card.on_finished(self)

	@gen.coroutine
	def react(self):
		selection = yield self.played_by.select(1, 1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to prevent attack?")
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			self.played_by.protection = 1

	def log_string(self, plural=False):
		return "".join(["<span class='label label-reaction'>", self.title, "s</span>" if plural else "</span>"])


# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

class Village(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Village"
		self.description = "{}{}".format(crd.format_draw(1), crd.format_actions(2))
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
		self.description = "{}You may immediately put your deck into your discard pile".format(crd.format_money(2))
		self.price = 3
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		selection = yield self.played_by.select(1, 1, ["Yes", "No"],  
			"Put your deck into your discard pile?")
		if selection[0] == "Yes":
			self.game.announce("-- puting their deck into their discard pile")
			self.played_by.discard_pile += self.played_by.deck
			self.played_by.deck = []
			self.played_by.update_discard_size()
			self.played_by.update_deck_size()
		crd.Card.on_finished(self)

class Woodcutter(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Woodcutter"
		self.description = "{}{}".format(crd.format_money(2), crd.format_buys(1))
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

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		gaining_list = yield self.played_by.select_from_supply("Select a card to gain costing up to $4", lambda x : x.get_price() <= 4)
		if gaining_list:
			yield self.played_by.gain(gaining_list[0])
		crd.Card.on_finished(self, False, False)

# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------

class Bureaucrat(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Bureaucrat"
		self.description = "Gain a Silver, put it on top of your deck. Each other player reveals a Victory card and puts it on their deck or reveals a hand with no Victory cards."
		self.price = 4

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.gain_to_deck("Silver")
		self.played_by.update_resources()
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	@gen.coroutine
	def attack(self):
		for i in self.played_by.get_opponents():
			if not crd.AttackCard.is_blocked(self, i):
				i_victory_cards = i.hand.get_cards_by_type("Victory")
				if len(i_victory_cards) == 0:
					self.game.announce(i.name_string() + " has no Victory cards & reveals " + i.hand.reveal_string())
				elif len(set(map(lambda x: x.title, i_victory_cards))) == 1:
					self.game.announce(i.name_string() + " puts " + i_victory_cards[0].log_string() + " back on top of the deck")
					yield i.discard([i_victory_cards[0].title], i.deck)
				else:
					self.played_by.wait("to choose a Victory card to put back", i)
					order_selection = yield i.select(1, 1, crd.card_list_to_titles(i_victory_cards),
						"select Victory card to put back")
					yield i.discard(order_selection, i.deck)
					self.game.announce(i.name_string() + " puts " + self.game.card_from_title(order_selection[0]).log_string() + " back on top of the deck")
					if not self.played_by.is_waiting():
						crd.Card.on_finished(self, False, False)
		if not self.played_by.is_waiting():
			crd.Card.on_finished(self, False, False)

class Feast(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Feast"
		self.type = "Action"
		self.description = "Trash this card, gain a card costing up to $5."
		self.price = 4

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		if self.played_by.played_cards[-1] == self:
			self.game.trash_pile.append(self.played_by.played_cards.pop())
			self.game.update_trash_pile()
			self.game.announce("-- trashing " + self.log_string())
		self.played_by.update_resources()
		selection = yield self.played_by.select_from_supply("Select a card to gain from Feast", lambda x : x.get_price() <= 5)
		if selection:
			yield self.played_by.gain(selection[0])
		crd.Card.on_finished(self, False, False)

class Gardens(crd.VictoryCard):
	def __init__(self, game, played_by):
		crd.VictoryCard.__init__(self, game, played_by)
		self.title = "Gardens"
		self.description = "{} for every 10 cards in your deck (rounded down)".format(crd.format_vp(1, True))
		self.price = 4
		self.vp = 0

	def get_vp(self):
		return int(self.played_by.total_deck_size() / 10)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-victory'>", self.title, "</span>"])


class Militia(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Militia"
		self.description = "{}Each other player discards down to 3 cards in hand.".format(crd.format_money(2))
		self.price = 4
		self.type = "Action|Attack"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.update_resources()
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())
		
	@gen.coroutine
	def attack(self):
		affected = [x for x in self.played_by.get_opponents() if not crd.AttackCard.is_blocked(self, x)]
		if affected:
			yield crd.discard_down(affected, 3)
		crd.Card.on_finished(self, False, False)

class Moneylender(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Moneylender"
		self.description = "trash a copper from your hand, if you do {}".format(crd.format_money(3, True))
		self.price = 4
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		if "Copper" in self.played_by.hand:
			yield self.played_by.discard(["Copper"], self.game.trash_pile)
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

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		 "select card to remodel")
		if selection:
			self.played_by.update_resources()
			yield self.played_by.discard(selection, self.game.trash_pile)
			card_trashed = self.game.card_from_title(selection[0])
			self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
			gain_list = yield self.played_by.select_from_supply("Select a card to gain from Remodel", lambda x : x.get_price() <= card_trashed.get_price() + 2)
			if gain_list:
				yield self.played_by.gain(gain_list[0])
				crd.Card.on_finished(self, False, False)
		else:
			crd.Card.on_finished(self)

class Spy(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Spy"
		self.description = "{}{}Each player (including you) reveals the top card of \
			their deck and either discards it or puts it back, your choice".format(crd.format_draw(1), crd.format_actions(1))
		self.price = 4

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- getting +1 action and drawing " + drawn)
		self.played_by.update_resources()
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	@gen.coroutine
	def attack(self):
		yield self.fire(self.played_by)

	@gen.coroutine
	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			if len(player.deck) < 1:
				player.shuffle_discard_to_deck()
				if len(player.deck) < 1:
					self.game.announce(player.name_string() + " has no cards to Spy.")
					crd.AttackCard.get_next(self, player)
					return
			revealed_card = player.deck[-1]
			selection = yield self.played_by.select(1, 1, ["discard", "keep"],
				player.name + " revealed " + revealed_card.title)
			if selection[0] == "discard":
				card = yield player.discard_topdeck()
				self.game.announce(self.played_by.name_string() + " discards " + card.log_string() + " from " +
					player.name_string() + "'s deck")
			else:
				card = player.deck[-1]
				self.game.announce(self.played_by.name_string() + " leaves " + card.log_string() + " on " +
					player.name_string() + "'s deck")
			crd.AttackCard.get_next(self, player)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-attack'>", "Spies" if plural else self.title, "</span>"])

class Smithy(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Smithy"
		self.description = "{}".format(crd.format_draw(3))
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(3)
		self.game.announce("-- drawing " + drawn)
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-action'>", "Smithies" if plural else self.title, "</span>"])

class Thief(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Thief"
		self.description = "Each other player reveals and discards the top 2 cards of their deck. If they revealed any Treasure cards,"\
			"they trash one that you choose and you may gain the trashed card."
		self.price = 4

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	@gen.coroutine
	def attack(self):
		yield crd.AttackCard.get_next(self, self.played_by)

	@gen.coroutine
	def fire(self, player):
		if crd.AttackCard.fire(self, player):
			revealed_cards = [player.topdeck(), player.topdeck()]
			if not any(revealed_cards):
				self.game.announce(player.name_string() + " has no cards to Thieve.")
				yield crd.AttackCard.get_next(self, player)
				return
			revealed_treasure = [x for x in revealed_cards if "Treasure" in x.type]

			self.game.announce(player.name_string() + " revealed "
				+ ", ".join([x.log_string() for x in revealed_cards]))
			if len(revealed_treasure) > 0:
				if len(revealed_treasure) == 1 or revealed_treasure[0].title == revealed_treasure[1].title:
					self.game.trash_pile.append(revealed_treasure[0])
					self.game.update_trash_pile()
					if revealed_cards[0] == revealed_treasure[0]:
						yield player.discard_floating(revealed_cards[1])
					else:
						yield player.discard_floating(revealed_cards[0])

					self.game.announce(player.name_string() + " trashes "
					+ revealed_treasure[0].log_string())

					steal_trashed = yield self.played_by.select(1, 1, ["Yes", "No"],
						"Gain " + revealed_treasure[0].title + "?")
					yield self.post_select_gain(steal_trashed, player, revealed_treasure[0].title)
				else:
					select_trash = yield self.played_by.select(1, 1, crd.card_list_to_titles(revealed_treasure),
						"Choose " + player.name + "'s Treasure to trash")
					yield self.post_select_trash(select_trash, player, revealed_treasure)
			else:
				#if no treasure, add the revealed cards to the discard
				yield player.discard_floating(revealed_cards)
				yield crd.AttackCard.get_next(self, player)

	@gen.coroutine
	def post_select_gain(self, selection, thieved, card):
		if selection[0] == "Yes":
			self.game.trash_pile.pop()
			self.game.update_trash_pile()
			yield self.played_by.gain(card, False)
		yield crd.AttackCard.get_next(self, thieved)

	@gen.coroutine
	def post_select_trash(self, selection, thieved, cards):
		card_to_trash = [x for x in cards if selection[0] == x.title][0]
		cards.remove(card_to_trash)
		self.game.trash_pile.append(card_to_trash)
		self.game.update_trash_pile()
		yield thieved.discard_floating(cards[0])
		self.game.announce(self.played_by.name_string() + " trashes " + card_to_trash.log_string() + " from " +
				thieved.name_string() + "'s deck")
		self.game.announce(thieved.name_string() + " discards " + cards[0].log_string() + " from their deck")
		steal_trashed = yield self.played_by.select(1, 1, ["Yes", "No"], "Gain " + card_to_trash.title + "?")
		yield self.post_select_gain(steal_trashed, thieved, card_to_trash.title)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-attack'>", "Thieves" if plural else self.title, "</span>"])


class Throne_Room(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Throne Room"
		self.description = "Choose an action card from your hand. Play it twice."
		self.price = 4
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		action_cards = self.played_by.hand.get_cards_by_type("Action")
		self.played_by.update_resources()
		selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(action_cards),
		 "select card for Throne Room")
		if not selection:
			self.game.announce(" -- but has no action cards")
			crd.Card.on_finished(self, False, False)
		else:
			selected_card = self.played_by.hand.extract(selection[0])
			throne_room_str = self.played_by.name_string() + " " + self.log_string(True) + " " + selected_card.log_string()
			on_duration = "Duration" in selected_card.type
			if not on_duration:
				self.played_by.played_cards.append(selected_card)
			else:
				self.played_by.played_cards.pop()
				self.played_by.durations.append(self)
				self.played_by.durations.append(selected_card)
				self.game.update_duration_mat()
			for i in range(0, 2):
				self.game.announce(throne_room_str)
				yield gen.maybe_future(selected_card.play(True))
				self.played_by.update_resources()
				self.played_by.update_hand()
			crd.Card.on_finished(self, False, False)

	@gen.coroutine
	def duration(self):
		selected_duration = self.played_by.durations.pop(0)
		throne_room_str = "{} resolves {}".format(self.log_string(), selected_duration.log_string())
		self.game.announce(throne_room_str)
		for i in range(0, 2):
			yield gen.maybe_future(selected_duration.duration())
		self.played_by.played_cards.append(selected_duration)

# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Council_Room(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Council Room"
		self.description = "{}{} Each other player draws a card".format(crd.format_draw(4), crd.format_buys(1))
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(4)
		self.played_by.buys += 1
		self.game.announce("-- drawing " + drawn + " and getting +1 buy")
		self.game.announce("-- each other player draws a card")
		for i in self.played_by.get_opponents():
			i.draw(1)
		crd.Card.on_finished(self)


class Festival(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Festival"
		self.description = "{}{}{}".format(crd.format_money(2), crd.format_actions(2),crd.format_buys(1))
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
		self.description = "{}{}".format(crd.format_draw(2), crd.format_actions(1))
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.played_by.actions += 1
		self.game.announce("-- drawing " + drawn + " and gaining +1 action")
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-action'>", "Laboratories" if plural else self.title, "</span>"])


class Library(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Library"
		self.description = "Draw until you have 7 cards in hand. You may set aside any action cards drawn this way. Discard the set aside cards after drawing"
		self.price = 5
		self.type = "Action"
		self.set_aside = []

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		while len(self.played_by.hand) < 7:
			top_card = self.played_by.topdeck()
			if top_card != None:
				if "Action" in top_card.type:
					set_aside = yield self.played_by.select(1, 1, ["Yes", "No"], "set aside " + top_card.title + "?")
					if set_aside[0] == "No":
						self.played_by.announce_self("-- You draw " + top_card.log_string())
						self.played_by.hand.add(top_card)
						self.played_by.update_hand()
					else:
						self.played_by.announce_self("-- You set aside " + top_card.log_string())
						self.set_aside.append(top_card)
					self.played_by.update_deck_size()
					self.played_by.update_discard_size()
					if len(self.played_by.hand) < 7:
						self.play(True)
					else:
						yield self.on_finish()
					return
				else:
					self.played_by.announce_self("-- You draw " + top_card.log_string())
					self.played_by.announce_opponents(msg="-- drawing 1 card")
					self.played_by.hand.add(top_card)
					self.played_by.update_hand()
			else:
				self.played_by.announce_self("-- You have no cards left to draw")
				break
		yield self.on_finish()

	@gen.coroutine
	def on_finish(self):
		yield self.played_by.discard_floating(self.set_aside)
		self.set_aside = []
		crd.Card.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-action'>", "Libraries" if plural else self.title, "</span>"])


class Market(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Market"
		self.description = "{}{}{}{}".format(crd.format_draw(1), crd.format_actions(1), 
				crd.format_buys(1), crd.format_money(1))
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(1)
		self.played_by.actions += 1
		self.played_by.balance += 1
		self.played_by.buys += 1
		self.game.announce("-- drawing " + drawn + " , gaining +1 action and $1")
		crd.Card.on_finished(self)


class Mine(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Mine"
		self.description = "Trash a Treasure card from your hand. Gain a Treasure card costing up to $3 more;"\
		"put it into your hand."
		self.price = 5
		self.type = "Action"

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		treasure_cards = self.played_by.hand.get_cards_by_type("Treasure")
		if len(treasure_cards) > 0:
			selection = yield self.played_by.select(1, 1, crd.card_list_to_titles(treasure_cards),
			 "select treasure to trash")
			if selection:
				yield self.played_by.discard(selection, self.game.trash_pile)
				card_trashed = self.game.card_from_title(selection[0])
				self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
				gain_treasure = yield self.played_by.select_from_supply("Select a treasure to gain", 
					lambda x : x.get_price() <= card_trashed.get_price() + 3 and "Treasure" in x.type)
				if gain_treasure:
					yield self.played_by.gain_to_hand(gain_treasure[0])
			crd.Card.on_finished(self, False, False)
		else:
			self.game.announce("-- but has no treasure cards to trash")
			crd.Card.on_finished(self)

class Witch(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Witch"
		self.description = "{}Each other player gains a curse card".format(crd.format_draw(2))
		self.price = 5

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.game.announce("-- drawing " + drawn)
		self.played_by.update_resources()
		yield crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	@gen.coroutine
	def attack(self):
		yield crd.AttackCard.get_next(self, self.played_by)

	@gen.coroutine
	def fire(self, victim):
		if not crd.AttackCard.is_blocked(self, victim):
			yield victim.gain("Curse")
		yield crd.AttackCard.get_next(self, victim)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-attack'>", self.title, "es</span>" if plural else "</span>"])


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

	@gen.coroutine
	def play(self, skip=False):
		crd.Card.play(self, skip)
		to_discard = []
		treasures = []
		if len(self.played_by.deck) == 0:
			self.played_by.shuffle_discard_to_deck()
		while len(self.played_by.deck) > 0:
			card = self.played_by.topdeck()
			if "Treasure" in card.type:
				treasures.append(card)
				if len(treasures) == 2:
					self.game.announce(self.played_by.name_string() + " reveals " + " , ".join(crd.card_list_log_strings(to_discard + treasures)))
					self.game.announce(self.played_by.name_string() + " puts " + " , ".join(crd.card_list_log_strings(treasures)) + " in hand")
					yield self.played_by.discard_floating(to_discard)
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
		yield self.played_by.discard_floating(to_discard)
		for t in treasures:
			self.played_by.hand.add(t)
		crd.Card.on_finished(self)

