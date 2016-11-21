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

	# called at the end of turn if this card was played
	# note only called a maximum of once for each card class played
	# i.e. playing 3 schemes fires Scheme's cleanup function to be called once
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

	def log_string(self, plural=False):
		return "".join(["<span class='label label-action'>", self.title, "s</span>" if plural else "</span>"])

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
		return "".join(["<span class='label label-treasure'>", self.title, "s</span>" if plural else "</span>"])


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
			yield gen.maybe_future(self.attack())
		else:
			self.played_by.wait_many("to react", reacting_players, True)
			#fire all the reactions in parallel
			yield parallel_selects(reaction_futures, reacting_players, lambda x,y: y.update_mode())
			yield gen.maybe_future(self.attack())

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
		return "".join(["<span class='label label-attack'>", self.title, "s</span>" if plural else "</span>"])

class Duration(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Action|Duration"

	def play(self, skip=False):
		self.played_by.played_inclusive.append(self)
		if not skip:
			self.played_by.discard([self.title], self.played_by.durations)
			self.game.announce(self.played_by.name_string() + " played " + self.log_string())
			self.played_by.actions -= 1
			self.game.update_duration_mat()

	def duration(self):
		self.game.announce("{} duration effect resolves".format(self.log_string()))

	def on_finished(self, modified_hand=True, modified_resources=True, waiting_cleanup=True):
		self.played_by.duration_cbs.append(self.duration)
		Card.on_finished(self, modified_hand, modified_resources, waiting_cleanup)

	def log_string(self, plural=False):
		return "".join(["<span class='label label-duration'>", self.title, "s</span>" if plural else "</span>"])

class VictoryCard(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Victory"

	def get_vp(self):
		return self.vp

	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-victory'>", self.title, "s</span>" if plural else "</span>"])

# Utility
#format game resources used for card descriptions
def format_actions(num_actions, inline=False):
	return "<b>+{} action{}</b>{}".format(num_actions, "s" if num_actions > 1 else "", "" if inline else "\n")

def format_buys(num_buys, inline=False):
	return "<b>+{} buy{}</b>{}".format(num_buys, "s" if num_buys > 1 else "", "" if inline else "\n")

def format_money(num_money, inline=False):
	return "<b>+${}</b>{}".format(num_money, "" if inline else "\n")

def format_draw(num_cards, inline=False):
	return "<b>+{} card{}</b>{}".format(num_cards, "s" if num_cards > 1 else "", "" if inline else "\n")

def format_vp(num_vp, inline=False):
	return "<b>{} VP</b>{}".format(num_vp, "" if inline else "\n")

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
		yield gen.maybe_future(callback(selected, selecting_player))

# asks player to reorder input list of cards
# player = player who is reordering
# cards_to_reorder = list of card objects have already been removed from the top of deck
@gen.coroutine
def reorder_top(player, cards_to_reorder):
	if len(cards_to_reorder) == 0:
		return
	elif len(set(map(lambda x: x.title, cards_to_reorder))) == 1:
		player.deck += cards_to_reorder
		player.update_deck_size()
		return
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

#search through a players deck and discard until findng a specific card
# player = player who owns deck to search through
# search_criteria = function that needs to accept a card object as a parameter and return True if the card object matches
#     what we are looking for False otherwise
@gen.coroutine
def search_deck_for(player, search_criteria):
	total_deck_count = len(player.discard_pile) + len(player.deck)
	discarded = list()
	match_found = False
	while match_found == False and len(discarded) < total_deck_count:
		topdeck = player.topdeck()
		if search_criteria(topdeck):
			match_found = True
		else:
			discarded.append(topdeck)
	
	if len(discarded) > 0:
		yield player.discard_floating(discarded)
		player.game.announce("-- discarding " + ", ".join(map(lambda card : card.log_string(), discarded)))
	if match_found:
		return topdeck

# prompts input players to discard down to input hand size
# players = list of players who needs to discard
# reduced_hand_size = number of cards to discard down to
@gen.coroutine
def discard_down(players, reduced_hand_size):
	if not players:
		return
	
	@gen.coroutine
	def discard_down_cb(selection, player):
		player.game.announce("-- " + player.name_string() + " discards down to " + str(reduced_hand_size))
		yield player.discard(selection, player.discard_pile)

	turn_owner = players[0].game.get_turn_owner()
	discarding_players = [x for x in players if len(x.hand) > reduced_hand_size]
	for i in [x for x in players if x not in discarding_players]:
		i.game.announce("-- " + i.name_string() + " has " + str(reduced_hand_size) + " or less cards in hand")

	if discarding_players:
		turn_owner.wait_many("to discard", discarding_players)
		futures = []
		for x in discarding_players:
			num_discarding = len(x.hand) - reduced_hand_size
			futures.append(x.select(num_discarding, num_discarding,
				card_list_to_titles(x.hand.card_array()), "choose " + str(num_discarding) + " cards to discard"))
		yield parallel_selects(futures , discarding_players, discard_down_cb)

