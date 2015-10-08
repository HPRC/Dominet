import tornado.gen as gen

class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None
		self.price = 0

		# setting lifecycle methods as attributes allows the methods to be unbound and able to dynamically bound at runtime or
		# at supply initialization
		self.on_buy = self.__class__.on_buy
		self.on_gain = self.__class__.on_gain

	def play(self, skip=False):
		if "Action" in self.type:
			self.played_by.played_inclusive.append(self)
		if not skip:
			self.played_by.discard([self.title], self.played_by.played_cards)
			self.game.announce(self.played_by.name_string() + " played " + self.log_string())
			if "Action" in self.type:
				self.played_by.actions -= 1


	def get_price(self):
		return 0 if self.price + self.game.price_modifier[self.title] < 0 else self.price + self.game.price_modifier[self.title]

	# called at the end of a card's resolution
	def on_finished(self, modified_hand=True, modified_resources=True, waiting_cleanup=True):
		if modified_resources:
			self.played_by.update_resources()
		if modified_hand:
			self.played_by.update_hand()
		self.played_by.update_mode()
		if waiting_cleanup:
			self.played_by.cb = None
		self.done()

	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price
		}

	#called when chosen for kingdom
	def on_supply_init(self):
		pass

	#called at the end of turn if this card was played
	def cleanup(self):
		pass

	#called when you buy this card 
	@gen.coroutine
	def on_buy(self):
		pass

	#called when you buy a card with this card in play
	@gen.coroutine
	def on_buy_effect(self, purchased_card):
		pass

	#called when you gain this card
	@gen.coroutine
	def on_gain(self):
		pass

	#called when you gain a card with this card in play
	@gen.coroutine
	def on_gain_effect(self, gained_card):
		pass

	#called after card finishes resolving and is put into the played_cards pile
	def done(self):
		pass

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", self.title, "s</span>" if plural else "</span>"])



class Money(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Treasure"
		self.value = None
		self.spend_all = True

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

	#This isn't called for basic money cards like gold/silver/copper/harem
	def on_finished(self):
		self.played_by.update_resources(True)
		
	# override
	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price,
			"value": self.value,
			"spend_all": self.get_spend_all()
		}

	def get_spend_all(self):
		return self.spend_all

	def log_string(self, plural=False):
		return "".join(["<span class='label label-warning'>", self.title, "s</span>" if plural else "</span>"])


class AttackCard(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Action|Attack"

	@gen.coroutine
	def check_reactions(self, targets):
		reaction_futures = []
		reacting_players = []
		for i in targets:
			if len(i.hand.get_reactions_for("Attack")) > 0:
				reacting_players.append(i)
				reaction_futures.append(i.hand.do_reactions("Attack"))
		if not reacting_players:
			self.attack()
		else:
			self.played_by.wait_many("to react", reacting_players, True)
			#fire all the reactions in parallel
			yield reaction_futures
			self.attack()

	def is_blocked(self, target):
		# shouldnt need to block against own attacks (i.e. spy)
		if target.protection == 0 or target == self.played_by:
			return False
		else:
			target.protection -= 1
			self.game.announce(target.name_string() + " is unaffected by the attack")
			return True

	# used in cards where we have to wait on each player to make a selection or something
	# if not blocked then continue the attack and a post_select or choice will trigger the get_next
	def fire(self, player):
		if not self.is_blocked(player):
			return True
		else:
			self.get_next(player)
	
	# should call get next of player of the attack first (or player if inclusive)
	# chooses the next person from the last until we reach the player to stop
	@gen.coroutine
	def get_next(self, victim):
		next_player_index = (self.game.players.index(victim) + 1) % len(self.game.players)
		if self.game.players[next_player_index] != self.played_by:
			yield gen.maybe_future(self.fire(self.game.players[next_player_index]))
		else:
			Card.on_finished(self)

	def attack(self):
		pass

	def log_string(self, plural=False):
		return "".join(["<span class='label label-danger'>", self.title, "s</span>" if plural else "</span>"])


class Copper(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Copper"
		self.value = 1
		self.price = 0
		self.description = "+$1"

	def play(self, skip=False):
		Money.play(self, skip)
		if "Grand Market" in self.game.supply and "Grand Market" not in self.played_by.banned:
			self.played_by.banned.append("Grand Market")
			self.played_by.update_mode_buy_phase()

	def get_spend_all(self):
		if "Grand Market" in self.game.supply and self.played_by is not None:
			spend_all_treasures = [x for x in self.played_by.hand.get_cards_by_type("Treasure", True) if x.title != "Copper" and x.get_spend_all()]
			potential_balance = 0
			for x in spend_all_treasures:
				potential_balance += x.value
			if self.played_by.balance >=6 or potential_balance + self.played_by.balance >=6:
				return False
			else:
				return True
		else:
			return True

class Silver(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Silver"
		self.value = 2
		self.price = 3
		self.description = "+$2"


class Gold(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Gold"
		self.value = 3
		self.price = 6
		self.description = "+$3"


class Platinum(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Platinum"
		self.value = 5
		self.price = 9
		self.description = "+$5"


class Curse(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Curse"
		self.description = "-1 VP"
		self.price = 0
		self.vp = -1
		self.type = "Curse"

	def get_vp(self):
		return self.vp
		
	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-curse'>", self.title, "s</span>" if plural else "</span>"])


class VictoryCard(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Victory"

	def get_vp(self):
		return self.vp

	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", self.title, "s</span>" if plural else "</span>"])


class Estate(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Estate"
		self.description = "1 VP"
		self.price = 2
		self.vp = 1


class Duchy(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Duchy"
		self.description = "3 VP"
		self.price = 5
		self.vp = 3

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", "Duchies</span>" if plural else self.title, "</span>"])


class Province(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Province"
		self.description = "6 VP"
		self.price = 8
		self.vp = 6


class Colony(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Colony"
		self.description = "10 VP"
		self.price = 11
		self.vp = 10

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", "Colonies</span>" if plural else self.title, "</span>"])

# Utility
# returns list of card titles from list of card jsons or card objects
def card_list_to_titles(lst):
	if len(lst) == 0:
		return []
	return list(map(lambda x: x['title'], lst)) if isinstance(lst[0], dict) else list(map(lambda x: x.title, lst))

#returns list of html log_strings from a list of cards
def card_list_log_strings(lst):
	return list(map(lambda x: x.log_string(), lst))

# runs futures in parallel and call the callbacks with responses as they come in
# futures = list of futures
# players = list of players mapping to futures
# callback = function called with data and player params after player selects data
@gen.coroutine
def parallel_selects(futures, players, callback):
	wait_iterator = gen.WaitIterator(*futures) 
	while not wait_iterator.done():
		selected = yield wait_iterator.next()
		selecting_player_index = wait_iterator.current_index
		selecting_player = players[selecting_player_index]
		callback(selected, selecting_player)

# asks player to reorder input list of cards
# player = player who is reordering
# cards_to_reorder = list of card objects have already been removed from the top of deck
# callback = called when player finishes reordering the top of his/her deck
@gen.coroutine
def reorder_top(player, cards_to_reorder, callback):
	if len(cards_to_reorder) == 0:
		callback()
	elif len(set(map(lambda x: x.title, cards_to_reorder))) == 1:
		player.deck += cards_to_reorder
		player.update_deck_size()
		callback()
	else:
		turn_owner = player.game.get_turn_owner()
		if turn_owner != player:
			turn_owner.wait("to reorder cards", player)
		order = yield player.select(len(cards_to_reorder), len(cards_to_reorder), card_list_to_titles(cards_to_reorder), 
			"Rearrange the cards to put back on top of deck (#1 is on top)", True)
		for x in order:
			for y in cards_to_reorder:
				if x == y.title:
					player.deck.append(y)
					break
		player.update_deck_size()
		callback()

#search through a players deck and discard until findng a specific card
# player = player who owns deck to search through
# search_criteria = function that needs to accept a card object as a parameter and return True if the card object matches
#     what we are looking for False otherwise
# callback = callback function we will call after finding our match, passing in the matching card to it or None
def search_deck_for(player, search_criteria, callback):
	total_deck_count = len(player.discard_pile) + len(player.deck)
	discarded = list()
	match_found = False
	while match_found == False and len(discarded) < total_deck_count:
		topdeck = player.topdeck()
		if search_criteria(topdeck):
			match_found = True
		else:
			player.discard_pile.append(topdeck)
			discarded.append(topdeck.log_string())

	if len(discarded) > 0:
		player.game.announce("-- discarding " + ", ".join(discarded))
		player.update_discard_size()
		player.update_deck_size()
	if match_found:
		callback(topdeck)
	else:
		callback(None)

#makes the given player discard their hand down to the reduced hand size
# player = player who needs to discard
# reduced_hand_size = number of cards to discard down to
# callback = callback function called after player discarded, default is card on_finished
@gen.coroutine
def discard_down(player, reduced_hand_size, callback):
	turn_owner = player.game.get_turn_owner()
	if len(player.hand) > reduced_hand_size:
		turn_owner.wait("to discard", player)
		discard_selection = yield player.select(len(player.hand) - reduced_hand_size, len(player.hand) - reduced_hand_size, 
			card_list_to_titles(player.hand.card_array()), "discard down to " + str(reduced_hand_size) + " cards")
		player.game.announce("-- " + player.name_string() + " discards down to " + str(reduced_hand_size))
		player.discard(discard_selection, player.discard_pile)
		player.update_hand()
		callback()
	else:
		player.game.announce("-- " + player.name_string() + " has " + str(reduced_hand_size) + " or less cards in hand")
		callback()

