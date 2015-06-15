import card as crd
import math

# --------------------------------------------------------
# ------------------------ 3 Cost ------------------------
# --------------------------------------------------------

class Watchtower(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Watchtower"
		self.description = "Draw until you have 6 cards in hand. Whenever you gain a card, you may\
			reveal Watchtower to trash it or put it on top of your deck."
		self.price = 3
		self.type = "Action|Reaction"
		self.trigger = "Gain"
		self.reacted_to_callback = None

	def play(self, skip=False):
		crd.Card.play(self, skip)
		num_to_draw = 6 - len(self.played_by.hand)
		if num_to_draw > 0:
			drawn = self.played_by.draw(num_to_draw)
			self.game.announce("-- drawing " + drawn)
		else:
			self.game.announce("-- but already has at least 6 cards in hand")
		crd.Card.on_finished(self)

	def react(self, reacted_to_callback, to_gain):
		self.reacted_to_callback = reacted_to_callback
		turn_owner = self.game.get_turn_owner()
		if self.played_by != turn_owner:
			turn_owner.wait("Waiting for other players to react")
			#need to add two because we have two choices to make and don't want to preemptively update wait
			turn_owner.waiting["on"] += [self.played_by, self.played_by]

		self.played_by.select(1, 1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to trash " + to_gain.title + " or put it on top of deck?")
			
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_reveal

	def post_reveal(self, selection):
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			self.played_by.select(1, 1, ["Trash", "Put on top of deck"], "Choose to trash")
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.trash_or_gain
		else:
			#clear 2nd wait since we selected hide
			self.played_by.update_wait()
			temp = self.reacted_to_callback
			self.reacted_to_callback = None
			temp()

	def trash_or_gain(self, selection):
		to_gain = self.played_by.discard_pile.pop()
		if selection[0] == "Trash":
			self.game.announce("-- trashing " + to_gain.log_string() + " instead of gaining it")
			self.game.trash_pile.append(to_gain)
			self.game.update_trash_pile()
		else:
			self.game.announce("-- putting " + to_gain.log_string() + " on the top of their deck")
			self.played_by.deck.append(to_gain)
			self.played_by.update_deck_size()

		temp = self.reacted_to_callback
		self.reacted_to_callback = None
		temp()

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])

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
		self.spend_all = False

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
			crd.Money.on_finished(self)

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

		crd.Money.on_finished(self)

class Trade_Route(crd.Card):
	mat_value = 0

	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Trade Route"
		self.description = "+$1 per token on the trade route mat. Trash a card from your hand."\
							" Each victory card pile in supply begins with $1 token. When a card is first gained from the pile, move the token to the trade route mat."
		self.price = 3
		self.type = "Action"

	def on_supply_init(self):
		for supply_card in self.game.supply.unique_cards():
			if "Victory" in supply_card.type:
				#Here we store the on_gain function of this card and override it with our own gained_to_mat function
				default_on_gain_function = supply_card.on_gain
				supply_card.on_gain = lambda x=supply_card : self.gained_to_mat(x, default_on_gain_function)
		self.game.mat["Trade Route"] = ""

	#this is set to be the on_gain function for all cards with trade route tokens on it. It increases the mat value
	#when the card is gained the first time and then removes this function as the on_gain and resets it to the previous
	#function.
	def gained_to_mat(self, supply_card, previous_gain_func):
		Trade_Route.mat_value +=1
		self.game.mat["Trade Route"] += " " + supply_card.log_string()
		self.game.update_mat()
		supply_card.on_gain = previous_gain_func
		supply_card.on_gain()
		print(supply_card.title + " Called")

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += Trade_Route.mat_value
		self.played_by.buys += 1
		self.game.announce("-- gaining a buy and $" + str(self.mat_value))
		if self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Choose a card to trash"):
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.trash_select
		else:
			self.trash_select([])

	def trash_select(self, selection):
		trash = self.played_by.hand.extract(selection[0])
		self.game.trash_pile.append(trash)
		self.game.update_trash_pile()
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
		if self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()), "Choose a card to trash"):
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.vp_trash_select
		else:
			self.vp_trash_select([])

	def vp_trash_select(self, selection):
		if selection:
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
		self.title = "Worker's Village"
		self.description = "+1 Card; +2 Actions, +1 Buy"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.actions += 2
		self.played_by.buys += 1
		drawn = self.played_by.draw(1)

		self.game.announce("-- drawing " + drawn + " and gaining 2 actions and 1 buy")

		self.played_by.update_hand()
		crd.Card.on_finished(self)


class Talisman(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Talisman"
		self.description = "Worth $1.\nWhile this is in play, when you buy a card costing $4 or less" \
		                   " that is not a Victory card, gain a copy of it."
		self.price = 4
		self.value = 1
		self.type = "Treasure"
		self.spend_all = False

	def on_buy_effect(self, purchased_card):
		if purchased_card.get_price() <= 4 and "Victory" not in purchased_card.type:
			card = self.played_by.get_card_from_supply(purchased_card.title, True)
			if card is not None:
				self.played_by.discard_pile.append(card)
				self.played_by.update_discard_size()
				self.game.announce("-- gaining another " + card.log_string())
		crd.Money.on_finished(self)


class Quarry(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Quarry"
		self.description = "$1.\nWhile this is in play, Action cards cost $2 less" \
		                   " but not less than 0"
		self.price = 4
		self.value = 1
		self.type = "Treasure"
		self.spend_all = False

	def play(self, skip=False):
		crd.Money.play(self, skip)
		for x in self.game.price_modifier.keys():
			if "Action" in self.game.card_from_title(x).type:
				self.game.price_modifier[x] -= 2
		self.game.update_all_prices()
		crd.Money.on_finished(self)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-warning'>", "Quarries</span>" if plural else self.title + "</span>"])


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

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", "Cities</span>" if plural else self.title + "</span>"])


class Contraband(crd.Money):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Contraband"
		self.description = "+$3, +1 Buy \n The player to your left names a card, you cannot buy that card this turn."
		self.price = 5
		self.value = 3
		self.type = "Treasure"
		self.spend_all = False

	def play(self, skip=False):
		crd.Money.play(self, skip)
		self.played_by.buys += 1
		self.game.announce("-- gaining a buy")

		left_opponent = self.played_by.get_left_opponent()
		left_opponent.select_from_supply()
		left_opponent.waiting["on"].append(left_opponent)
		left_opponent.waiting["cb"] = self.contraband_select

		self.played_by.wait("Waiting for " + left_opponent.name + " to choose a card for contraband")
		self.played_by.waiting["on"].append(left_opponent)

	def contraband_select(self, selection):
		left_opponent = self.played_by.get_left_opponent()
		self.game.announce(left_opponent.name_string() + " bans " + self.game.log_string_from_title(selection[0]))
		self.played_by.banned.append(selection[0])
		crd.Money.on_finished(self)

class Counting_House(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Counting House"
		self.description = "Look through your discard pile, reveal any number of Copper cards from it, and put them into your hand."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		coppers = [x for x in self.played_by.discard_pile if x.title == "Copper"]
		if len(coppers) == 0:
			self.game.announce("-- but has no copper in their discard pile")
			crd.Card.on_finished(self, False, True)
		else:
			self.played_by.select(1, 1, [str(i) for i in range(0, len(coppers))], "Choose number of coppers to put into hand.")
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.select_copper

	def select_copper(self, selection):
		num_revealed = int(selection[0])
		added_to_hand = 0
		for i in range(len(self.played_by.discard_pile)-1, -1, -1):
			if added_to_hand == num_revealed:
				break
			elif self.played_by.discard_pile[i].title == "Copper":
				copper = self.played_by.discard_pile.pop(i)
				self.played_by.hand.add(copper)
				added_to_hand += 1
		self.played_by.update_hand()
		self.game.announce("-- removing " + str(selection[0]) + " coppers from their discard and putting them in hand.")
		self.played_by.update_discard_size()
		self.played_by.update_deck_size()
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
		treasures = list(set(map(lambda x: x.title, treasures)))

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
		self.played_by.gain(selection[0], done_gaining=lambda : crd.Card.on_finished(self, False, False))

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
				player.gain("Curse", done_gaining=
					lambda : player.gain("Copper", done_gaining=
						lambda : crd.AttackCard.get_next(self, player)))

	def post_select(self, selection, player):
		if selection[0] == "Yes":
			curse = player.hand.extract("Curse")
			player.update_hand()
			player.discard_pile.append(curse)
			self.game.announce("-- " + player.name_string() + " discards a " + curse.log_string())
			crd.AttackCard.get_next(self, player)
		else:
			player.gain("Curse", done_gaining=
				lambda : player.gain("Copper", done_gaining=
					lambda : crd.AttackCard.get_next(self, player)))


class Rabble(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Rabble"
		self.description = "+3 Cards\nEach other player reveals the top 3 cards of his deck, " \
		                   "discards the revealed Actions and Treasures, and puts the rest back " \
		                   "on top in any order he chooses."
		self.price = 5
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.AttackCard.play(self, skip)
		drawn = self.played_by.draw(3)
		self.played_by.update_hand()
		self.game.announce("-- drawing " + drawn)
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		attacking = False
		for player in self.played_by.get_opponents():
			if crd.AttackCard.fire(self, player):
				attacking = True
				if len(player.deck) < 3:
					player.shuffle_discard_to_deck()

				revealed = []
				if len(player.deck) < 3:
					revealed = player.deck
				else:
					revealed = player.deck[-3:]
				# removed the revealed cards from deck
				num_truncate = len(revealed)
				del player.deck[-num_truncate:]
				if len(revealed) != 0:
					self.game.announce(player.name_string() + " reveals " + ", ".join(list(map(lambda x: x.log_string(), revealed))))
				else:
					self.game.announce(player.name_string() + " reveals nothing")
				action_treasure_cards = [x for x in revealed if "Treasure" in x.type or "Action" in x.type]
				if len(action_treasure_cards) > 0:
					action_treasure_card_titles = [x.log_string() for x in action_treasure_cards]
					self.game.announce("-- discarding " + ", ".join(action_treasure_card_titles))
					for at in action_treasure_cards:
						player.discard_pile.append(at)
					player.update_deck_size()
					player.update_discard_size()

				cards_left = [x for x in revealed if "Action" not in x.type and "Treasure" not in x.type]
				crd.reorder_top(player, cards_left, self.finish)
		if not attacking:
			crd.Card.on_finished(self, False, False)

	def finish(self):
		if len(self.played_by.waiting["on"]) == 0:
			crd.Card.on_finished(self, False, False)

class Royal_Seal(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Royal Seal"
		self.description = "Worth $2\nWhile this is in play, when you gain a card," \
		                   " you may put that card on top of your deck."
		self.price = 5
		self.value = 2
		self.spend_all = False

	def on_buy_effect(self, purchased_card):
		self.played_by.select(1, 1, ["Yes", "No"], "Place " + purchased_card.title + " on top of deck?")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_buy

	def post_buy(self, selection):
		if selection[0] == "Yes":
			purchased_card = self.played_by.discard_pile.pop()
			self.game.announce(self.played_by.name_string() + " uses " + self.log_string() + " to place "
				+ purchased_card.log_string() + " on the top of their deck")
			self.played_by.deck.append(purchased_card)
		self.played_by.update_resources(True)

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
			#callback for each opponent
			def discard_choice_cb(selection, player=i):
				self.discard_choice(selection, player)

			self.played_by.waiting["on"].append(i)
			i.select(1, 1, ["Yes", "No"], "Discard 2 cards to draw 1?")
			i.waiting["on"].append(i)
			i.waiting["cb"] = discard_choice_cb

	def discard_choice(self, selection, player):
		if selection[0] == "Yes":
			def discard_select_cb(selection, player=player):
				self.discard_select(selection, player)

			player.select(min(len(player.hand.card_array()), 2), 2, crd.card_list_to_titles(player.hand.card_array()), "Discard up to 2")
			self.played_by.wait("Waiting for " + player.name + " to discard")
			self.played_by.waiting["on"].append(player)
			player.waiting["on"].append(player)
			player.waiting["cb"] = discard_select_cb
		elif len(self.played_by.waiting["on"]) == 0:
			crd.Card.on_finished(self, False, True)

	def discard_select(self, selection, player):
		player.discard(selection, player.discard_pile)
		drawn = 0
		if len(selection) >= 2:
			drawn = player.draw(1)
			player.update_hand()
		self.game.announce(player.name_string() + " discards " + str(len(selection)) + " cards and draws " + drawn)
		if len(self.played_by.waiting["on"]) == 0:
			crd.Card.on_finished(self)

class Venture(crd.Money):
	def __init__(self, game, played_by):
		crd.Money.__init__(self, game, played_by)
		self.title = "Venture"
		self.description = "Worth $1\nWhen you play this, reveal cards from your deck until you reveal a Treasure. " \
		                   "Discard the other cards. Play that Treasure."
		self.price = 5
		self.value = 1
		self.type = "Treasure"
		self.spend_all = False

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

		crd.search_deck_for(self.played_by, lambda x : "Treasure" in x.type, self.found)

	def found(self, card):
		if card is None:
			self.game.announce("-- but could not find any treasures in his or her deck.")
		else:
			self.game.announce("-- revealing " + card.log_string())
			self.game.announce("-- " + self.played_by.name_string() + " played " + card.log_string())
			card.play(True)
			self.played_by.played.append(card)
		crd.Money.on_finished(self)

# --------------------------------------------------------
# ------------------------ 6 Cost ------------------------
# --------------------------------------------------------


class Goons(crd.AttackCard):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Goons"
		self.description = "+1 Buy; +$2\nEach other player discards down to 3 cards in hand." \
		                   "\nWhile this is in play, when you buy a card, +1 VP token."
		self.price = 6
		self.type = "Action|Attack"

	def play(self, skip=False):
		crd.AttackCard.play(self, skip)
		self.played_by.balance += 2
		self.played_by.buys += 1

		self.game.announce("-- gaining +$2 and +1 Buy")
		self.played_by.update_resources()
		crd.AttackCard.check_reactions(self, self.played_by.get_opponents())

	def attack(self):
		attacking = False
		for i in self.played_by.get_opponents():
			if not crd.AttackCard.is_blocked(self, i):
				attacking = True
				crd.discard_down(i, 3, lambda : crd.Card.on_finished(self, False, False))
		if not attacking:
			crd.Card.on_finished(self, False, False)

	def on_buy_effect(self, purchased_card):
		self.played_by.vp += 1
		self.game.announce("-- gaining +1 VP")

	def log_string(self, plural=False):
		return "".join(["<span class='label label-danger'>", self.title, "</span>"])

class Hoard(crd.Money):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Hoard"
		self.description = "Worth $2.\n While this is in play, when you buy a Victory card, gain a Gold."
		self.price = 6
		self.value = 2
		self.type = "Treasure"
		self.spend_all = False

	def on_buy_effect(self, purchased_card):
		if "Victory" in purchased_card.type:
			self.played_by.gain("Gold", True, True, done_gaining= lambda : 
				self.game.announce("-- gaining a " + self.played_by.get_card_from_supply("Gold", False).log_string()))
		crd.Money.on_finished(self)

class Grand_Market(crd.Card):
	def __init__(self, game, played_by):
		crd.AttackCard.__init__(self, game, played_by)
		self.title = "Grand Market"
		self.description = "+1 Card, +1 Action, +1 Buy, +$2\n" \
							"You can't buy this card if you have copper in play"
		self.price = 6
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		drawn = self.played_by.draw(1)
		self.played_by.actions += 1
		self.played_by.balance += 2
		self.played_by.buys += 1
		self.game.announce("-- drawing " + drawn + " , gaining +1 action and $2")
		crd.Card.on_finished(self)

# --------------------------------------------------------
# ------------------------ 7 Cost ------------------------
# --------------------------------------------------------


class Bank(crd.Money):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Bank"
		self.description = "Worth $?\nWhen you play this, it’s worth $1 per Treasure card you have in play (counting this)."
		self.price = 7
		self.value = 0
		self.type = "Treasure"
		self.spend_all = False

	def play(self, skip=False):
		crd.Card.play(self, skip)
		total_played_treasures = 0
		for card in self.played_by.played:
			if "Treasure" in card.type:
				total_played_treasures += 1
		self.played_by.balance += total_played_treasures
		self.game.announce("-- gaining +$" + str(total_played_treasures))
		crd.Card.on_finished(self)


class Expand(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Expand"
		self.description = "Trash a card from your hand. Gain a card costing up to $3 more than the trashed card."
		self.price = 7
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		if self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),
		                      "select card to expand"):
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select
		else:
			self.game.announce("-- but has nothing to expand.")
			self.played_by.update_resources()

	def post_select(self, selection):
		self.played_by.discard(selection, self.game.trash_pile)
		card_trashed = self.game.card_from_title(selection[0])
		self.game.announce(self.played_by.name_string() + " trashes " + card_trashed.log_string())
		self.played_by.select_from_supply(card_trashed.price + 3, False)

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.update_hand()

	def post_gain(self, selected):
		self.played_by.gain(selected[0], done_gaining=lambda : crd.Card.on_finished(self, False, False))

class Kings_Court(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "King's Court"
		self.description = "Choose an action card from your hand. Play it three times."
		self.price = 7
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		action_cards = self.played_by.hand.get_cards_by_type("Action")
		if not self.played_by.select(1, 1, crd.card_list_to_titles(action_cards),
		 "select card for King's Court"):
			self.done = lambda : None
			self.game.announce(" -- but has no action cards")
		else:
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select
		self.played_by.update_resources()

	def post_select(self, selection):
		selected_card = self.played_by.hand.get_card(selection[0])
		kings_court_str = self.played_by.name_string() + " " + self.log_string(True) + " " + selected_card.log_string()

		def final_done(card=selected_card):
			# after the third play of card is finished, kings court is finished
			card.done = lambda: None
			crd.Card.on_finished(self, False, False)

		#plays the selected card 2nd and 3rd time, done_cb is the callback called after a card finishes playing
		#the default done cb is final_done to be called after the 3rd card is played.
		def play_again(card=selected_card, done_cb=final_done):
			card.game.announce(kings_court_str)
			card.done = done_cb
			card.play(True)
			card.played_by.update_resources()

		#after playing the card the first time, we set the done callback to play_again and override the default
		#done callback for the 2nd time the card is played to play_again to play a 3rd time
		selected_card.done = lambda : play_again(done_cb=play_again)
		self.played_by.discard(selection, self.played_by.played)
		self.game.announce(kings_court_str)
		selected_card.play(True)
		self.played_by.update_resources()
		self.played_by.update_hand()


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
		if self.played_by.select(None, len(self.played_by.hand.card_array()), 
			crd.card_list_to_titles(self.played_by.hand.card_array()), "Trash any number of cards"):
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.trash_select
		elif self.played_by.select_from_supply(price_limit=0, equal_only=True, optional=False):
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.gain_select
		else:
			crd.Card.on_finished(self)


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

		if self.played_by.select_from_supply(price_limit=trash_sum, equal_only=True, optional=False):
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.gain_select
		else:
			crd.Card.on_finished(self)

	def gain_select(self, selection):
		self.played_by.gain(selection[0], done_gaining=lambda : crd.Card.on_finished(self))


# --------------------------------------------------------
# ------------------------ 8 Cost ------------------------
# --------------------------------------------------------

class Peddler(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Peddler"
		self.description = "+1 Card, +1 Action, +$1\n" \
		                   "During your Buy phase, this costs $2 less for each action card in play (not less than $0)"
		self.price = 8
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- drawing " + drawn)
		self.played_by.actions += 1
		crd.Card.on_finished(self)

	#called when the buy phase begins
	def on_buy_phase(self):
		modifier = self.game.get_turn_owner().played_actions * -2
		self.game.price_modifier[self.title] = modifier
