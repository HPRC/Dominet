from collections import deque
import json
import sets.card as crd
import cardpile as cp
import random
import sets.base as b
import sets.supply as supply_cards
import sets.prosperity as prosperity
import sets.intrigue as intrigue
import sets.hinterlands as hl
import html
import game as g
import waitHandler as w

import tornado.concurrent
import tornado.gen as gen

class Client():
	hand_size = 5

	def __init__(self, name, c_id, handler):
		self.name = name
		self.id = c_id
		self.handler = handler
		self.game = None
		self.ready = False
		self.vp = 0

	# called before players take their turns
	def setup(self):
		pass

	def write_json(self, **kwargs):
		self.handler.write_json(**kwargs)
		if self.game is not None and kwargs["command"] != "announce":
			self.game.logger.log_json_data(str(self.name + ": " + json.dumps(kwargs)), True)

	def take_turn(self):
		self.write_json(command="startTurn")

	@gen.coroutine
	def exec_commands(self, data):
		cmd = data["command"]
		if self.game is None:
			if cmd == "chat":
				self.handler.chat(data["msg"], self.name)
			return
		self.game.logger.log_json_data(str(self.name + ": " + json.dumps(data)), False)


class DmClient(Client):

	def write_json(self, **kwargs):
		if kwargs["command"] == "updateMode":
			# ignore the last_mode if it was a wait for afk
			if not ("msg" in kwargs and "not responded" in kwargs["msg"]):
				# callback used to resume mode if reconnect
				self.last_mode = kwargs
		Client.write_json(self, **kwargs)

	def base_deck(self):
		deck = []
		for i in range(0, 7):
			deck.append(supply_cards.Copper(game=self.game, played_by=self))
		for i in range(0, 3):
			deck.append(supply_cards.Estate(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, num_cards, return_string=True):
		drawn = []
		if len(self.deck) < num_cards:
			self.shuffle_discard_to_deck()
		for i in range(0, num_cards):
			if len(self.deck) >= 1:
				card = self.deck.pop()
				drawn.append(card)
				self.hand.add(card)
		if not return_string:
			self.update_hand()
			self.update_deck_size()
			return drawn
		if len(drawn) == 0:
			return "nothing"
		elif len(drawn) == 1:
			self.update_deck_size()
			self.update_hand()
			return "a card"
		else:
			self.update_deck_size()
			self.update_hand()
			return str(len(drawn)) + " cards"

	# get top card of deck
	def topdeck(self):
		if len(self.deck) == 0:
			self.shuffle_discard_to_deck()
			if len(self.deck) == 0:
				return None
		return self.deck.pop()

	def shuffle_discard_to_deck(self):
		self.game.announce("<i>" + self.name_string() + " reshuffles</i>")
		random.shuffle(self.discard_pile)
		self.deck = self.discard_pile + self.deck
		self.discard_pile = []
		self.update_deck_size()
		self.update_discard_size()

	def setup(self):
		self.last_mode = {"command":"updateMode", "mode": "action"}
		self.discard_pile = []
		# deck = [bottom, middle, top]
		self.vp = 0
		self.deck = self.base_deck()
		self.hand = cp.HandPile(self)
		# actual cards played to be added back into deck, throne rooming a card does not add two cards to this
		self.played_cards = []
		# all cards played, if a card was throne roomed, it is added twice
		self.played_inclusive = []
		self.durations = []
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.draw(self.hand_size)
		self.waiter = w.WaitHandler(self)
		self.gamelog = []
		self.cb = None
		# input from client that was received when there wasn't a callback, stored and popped if available on next selection
		self.input_deque = deque()
		self.queue_choices = []
		self.protection = 0
		self.phase = "action"
		#boolean to keep track of if we bought a card to disable spending treasure afterwards
		self.bought_cards = False
		#cards banned from buying
		self.banned = []

	def update_hand(self):
		self.write_json(command="updateHand", hand=[x.to_json() for x in self.hand.card_array()])

	# override
	@gen.coroutine
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		while self.durations:
			d = self.durations.pop(0)
			yield gen.maybe_future(d.duration())
			self.played_cards.append(d)
		self.game.update_duration_mat()
		self.phase = "action"
		self.write_json(command="updateMode", mode="action")
		self.write_json(command="startTurn", actions=self.actions, buys=self.buys, 
			balance=self.balance)
		self.waiter.reset_afk_timer()

	# override
	@gen.coroutine
	def exec_commands(self, data):
		yield Client.exec_commands(self, data)
		#if we reconnected and an old connection is sending input, ignore
		if self.game is None:
			return
		cmd = data["command"]

		if cmd == "returnToLobby":
			self.handler.return_to_lobby()
			self.ready = False
			self.waiter.remove_afk_timer()
			self.game = None
			self.waiter = None
		elif cmd == "submitBugReport":
			self.game.logger.flag_me()
		elif cmd == "chat":
			self.game.chat(data["msg"], self.name)
		elif self.game.turn_count > 0:
			self.waiter.reset_afk_timer()

		#ingame player commands
		if cmd == "ready":
			self.ready = True
			#if game unstarted
			if self.game.turn_count == 0:
				if self.game.players_ready():
					self.game.turn_count = 1
					yield self.game.start_game()
			#else game started, we are reconnecting
			else:
				self.reconnect()
				yield self.resume()
		elif cmd == "play":
			if data["card"] not in self.hand:
				print("Error " + data["card"] + " not in Hand: " + ",".join(map(lambda x: x.title, self.hand.card_array())))
			else:
				yield self.hand.play(data["card"])
		elif cmd == "discard":
			yield self.discard(data["cards"], self.discard_pile)
		elif cmd == "endTurn":
			yield self.end_turn()
		elif cmd == "buyCard":
			yield self.buy_card(data["card"])
		elif cmd == "post_selection": 
			self.exec_selected_choice(data["selection"])
		elif cmd == "selectSupply":
			self.exec_selected_choice(data["card"])
		elif cmd == "spendAllMoney":
			yield self.spend_all_money()
			
	def exec_selected_choice(self, choice):
		self.update_wait()
		# if its my turn allow card that triggered selection to handle mode
		# else default update mode
		if self.game.get_turn_owner() != self:
			self.update_mode()
		# choice(the parameter) to waiting callback is 
		# a list for post_selection
		# a list for selectSupply
		# a string for buyCard
		if self.cb is not None:
			self.cb.set_result(choice)
			self.cb = None
		else:
			self.input_deque.append(choice)

	def reconnect(self):
		self.game.announce(self.name_string() + " has reconnected!")
		self.write_json(command="setGameLog", log="<br>".join(self.gamelog))
		self.game.load_supplies()
		self.update_hand()
		self.update_resources()
		self.game.update_trash_pile()

	@gen.coroutine
	def resume(self):
		afk_players = [x for x in self.game.players if x.waiter.is_afk]
		if afk_players:
			selected = yield self.select(1,1, ["Yes"],
					"{} {} not responded for over 5 minutes, force forefeit?".format(", ".join([i.name for i in afk_players]), "have" if len(afk_players) > 1 else "has"))
			if selected == ["Yes"]:
				self.game.end_game(afk_players)
		else:
			self.write_json(**self.last_mode)
		
		turn_owner = self.game.get_turn_owner()
		turn_owner.write_json(**turn_owner.last_mode)
		turn_owner.write_json(command="startTurn", actions=turn_owner.actions, buys=turn_owner.buys, 
			balance=turn_owner.balance)

	@gen.coroutine
	def end_turn(self):
		self.phase = "cleanup"
		yield self.discard(crd.card_list_to_titles(self.hand.card_array()), self.discard_pile)
		# cleanup before game ends
		unique_cards_played = {}
		for x in self.played_cards:
			unique_cards_played[x.title] = x
		# only call cleanup function once for each card even if a card was played multiple times
		for card_played in unique_cards_played.values():
			yield gen.maybe_future(card_played.cleanup())
		self.discard_pile = self.discard_pile + self.played_cards
		self.played_cards = []
		self.waiter.remove_afk_timer()
		if self.game.detect_end():
			return
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.played_inclusive = []
		self.bought_cards = False
		self.banned = []
		self.draw(self.hand_size)
		self.game.reset_prices()
		self.update_discard_size()
		self.update_deck_size()
		self.phase = None
		yield self.game.change_turn()

	#used to properly generate a copy of a card from supply to add to my deck
	def gen_new_card(self, card_title):
		supply_card = self.game.card_from_title(card_title)
		# we instantiate a new card by getting the class from the kingdom instance 
		# and instantiating it
		new_card = type(supply_card)(self.game, self)
		# patch the on buy and on gain functions in case they were overriden at supply initialization
		# used for example with trade route
		supply_card.played_by = self
		new_card.on_gain = supply_card.on_gain.__get__(new_card, crd.Card)
		new_card.on_buy = supply_card.on_buy.__get__(new_card, crd.Card)
		return new_card

	@gen.coroutine
	def buy_card(self, card_title):
		if self.buys > 0 and self.game.supply.get_count(card_title) > 0 and card_title not in self.banned:
			new_card = self.gen_new_card(card_title)
			self.game.announce("<b>" + self.name + "</b> buys " + new_card.log_string())
			self.buys -= 1
			self.balance -= new_card.get_price()
			self.bought_cards = True
			self.game.remove_from_supply(card_title)
			
			yield gen.maybe_future(new_card.on_buy())
			yield gen.maybe_future(self.resolve_on_buy_effects(new_card))
			yield self.gain_helper(new_card, False, None)
		self.update_resources(True)

	def select(self, min_cards, max_cards, select_from, msg, ordered=False):
		if len(select_from) > 0:
			self.write_json(command="updateMode", mode="select", min_cards=min_cards, max_cards=max_cards,
				select_from=select_from, msg=msg, ordered=ordered)

			if self.input_deque:
				return gen.maybe_future(self.input_deque.pop())
			future = tornado.concurrent.Future()
			self.cb = future
			return future
		else:
			return []

	#doesnt update mode to wait immediately
	def wait_modeless(self, msg, on, locked=False):
		self.waiter.append_wait(on)
		if locked:
			self.waiter.set_lock(on ,True)
		self.waiter.msg = msg

	def wait_many(self, msg, on, locked=False):
		for i in on:
			self.waiter.append_wait(i)
			#only change lock if we are locking, update_wait must be called to unlock
			if locked:
				self.waiter.set_lock(i ,True)
		self.waiter.wait(msg)


	def wait(self, msg, on, locked=False):
		self.waiter.append_wait(on)
		self.waiter.wait(msg)
		#only change lock if we are locking, update_wait must be called to unlock
		if locked:
			self.waiter.set_lock(on, True)

	def is_waiting(self):
		return self.waiter.is_waiting()

	#have all opponents wait on me
	def opponents_wait(self, msg, locked=False):
		for i in self.get_opponents():
			#only change lock if we are locking, update_wait must be called to unlock
			if locked:
				i.waiter.set_lock(self, locked)
			i.waiter.append_wait(self)
			i.waiter.wait(msg)

	#notify others that they should be done waiting on me
	#if unlocking need to update mode manually
	def update_wait(self, manually_called=False):
		for i in self.game.players:
			i.waiter.notify(self, manually_called)

	# assumes removed card from where discarding from beforehand
	@gen.coroutine
	def discard_floating(self, cards):
		if not isinstance(cards, list):
			cards = [cards]
		for x in cards:
			yield self.discard_reaction(x)
			self.discard_pile.append(x)
		self.update_deck_size()
		self.update_discard_size()

	@gen.coroutine
	def discard_topdeck(self):
		card = self.topdeck()
		if card is None:
			return
		yield self.discard_reaction(card)
		self.discard_pile.append(card)
		self.update_deck_size()
		self.update_discard_size()
		return card

	# cards = list of card titles
	@gen.coroutine
	def discard(self, cards, discard_to):
		for x in cards:
			card = self.hand.extract(x)
			if card is not None:
				if discard_to == self.discard_pile:
					yield self.discard_reaction(card)
				discard_to.append(card)
		self.update_hand()
		if discard_to == self.discard_pile:
			self.update_discard_size()	
		elif discard_to == self.game.trash_pile:
			self.game.update_trash_pile()

	@gen.coroutine
	def discard_reaction(self, card):
		if "Reaction" in card.type and card.trigger == "Discard":
			turn_owner = self.game.get_turn_owner()
			if self != turn_owner:
				turn_owner.wait("to react", self, True)
			yield card.react()
			self.update_wait(True)
		
	def update_mode(self):
		played_money = [x for x in self.played_cards if "Treasure" in x.type]
		# if we have no actions or no action cards and no money cards, buy mode
		if (len(self.hand.get_cards_by_type("Action")) == 0 or self.actions == 0) and len(self.hand.get_cards_by_type("Treasure")) == 0:
			self.update_mode_buy_phase()
		else:
			if not played_money and self.actions > 0 and len(self.hand.get_cards_by_type("Action")) != 0 and not self.bought_cards:
				self.write_json(command="updateMode", mode="action")
			else:
				self.update_mode_buy_phase()

	def update_mode_buy_phase(self):
		if (self.phase != "buy"):
			#initalize buy phase code here
			if "Peddler" in self.game.supply and self.game.get_turn_owner() == self:
				self.game.card_from_title("Peddler").on_buy_phase()
				self.game.update_all_prices()

		self.phase = "buy"
		self.write_json(command="updateMode", mode="buy", bought_cards=self.bought_cards, banned=self.banned)

	def update_deck_size(self):
		self.write_json(command="updateDeckSize", size=len(self.deck))

	def update_discard_size(self):
		self.write_json(command="updateDiscardSize", size=len(self.discard_pile))

	def get_card_from_supply(self, card, from_supply=True):
		if self.game.supply.get_count(card) <= 0 and from_supply:
			return
		if from_supply:
			self.game.remove_from_supply(card)
		return self.gen_new_card(card)

	@gen.coroutine
	def gain_helper(self, card_obj, from_supply=True, announcement=None):
		if announcement is not None and announcement is not "":
			self.game.announce(announcement)
		self.discard_pile.append(card_obj)
		self.update_discard_size()
		yield gen.maybe_future(card_obj.on_gain())
		yield gen.maybe_future(self.hand.do_reactions("Gain", card_obj))
		for i in self.get_opponents():
			yield gen.maybe_future(i.hand.do_reactions("OpponentGain", card_obj))
		if card_obj in self.all_cards():
			yield gen.maybe_future(self.resolve_on_gain_effects(card_obj))

	@gen.coroutine
	def gain(self, card, from_supply=True, custom_announce=None):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			if custom_announce is None:
				yield self.gain_helper(new_card, from_supply, self.name_string() + " gains " + new_card.log_string())
			else:
				yield self.gain_helper(new_card, from_supply, custom_announce)
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + " but it is out of supply.")

	@gen.coroutine
	def gain_to_deck(self, card, from_supply=True):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			yield self.gain_helper(new_card, from_supply, "{} gains {} and puts it on top of their deck.".format(
				self.name_string(), new_card.log_string()))
			#if the gained card is still in discard pile, then we can remove and add to deck
			if self.discard_pile and new_card == self.discard_pile[-1]:
				self.deck.append(self.discard_pile.pop())
				self.update_deck_size()
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + " but it is out of supply.")

	@gen.coroutine
	def gain_to_hand(self, card, from_supply=True):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			yield self.gain_helper(new_card, from_supply, self.name_string() + " gains " + new_card.log_string() + " to their hand.")
			#if the gained card is still in discard pile, then we can remove and add to hand
			if self.discard_pile and new_card == self.discard_pile[-1]:
				self.hand.add(self.discard_pile.pop())
				self.update_hand()
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + " but it is out of supply.")

	def select_from_supply(self, msg, constraint=lambda x: True, allow_empty=False, optional=False):
		avail = self.game.supply.has_selectable(constraint, allow_empty)
		if allow_empty or avail:
			self.write_json(command="updateMode", mode="selectSupply", msg=msg, allowed=crd.card_list_to_titles(avail), 
				optional=optional)

			if self.input_deque:
				return gen.maybe_future(self.input_deque.pop())
			future = tornado.concurrent.Future()
			self.cb = future
			return future
		else:
			self.game.announce("-- but there is nothing available in supply")
			return []

	def get_duration_string(self):
		if self.durations:
			return "{}: {}".format(self.name_string(), ", ".join(crd.card_list_log_strings(self.durations)))
		return ""

	def update_resources(self, playedMoney=False):
		if playedMoney:
			self.update_mode_buy_phase()
		self.write_json(command="updateResources", actions=self.actions, buys=self.buys, balance=self.balance)

	# searches all player's cards for specific card object and removes and returns it (if found)
	def search_and_extract_card(self, card):
		try:
			self.deck.remove(card)
			self.update_deck_size()
			return card
		except ValueError:
			pass
		try:
			self.discard_pile.remove(card)
			self.update_discard_size()	
			return card
		except ValueError:
			pass
		for x in self.hand:
			if x == card:
				return self.hand.extract_specific(x)
		try:
			self.played_cards.remove(card)
			return card
		except ValueError:
			pass
		return None


	def total_deck_size(self):
		return len(self.deck) + len(self.discard_pile) + len(self.played_cards) + len(self.hand)

	#by default returns list in order starting with players after you
	def get_opponents(self):
		try:
			my_index = self.game.players.index(self)
		except ValueError:
			return []
		opponents = []
		for i in range(1, len(self.game.players)):
			opponents.append(self.game.players[(my_index + i) % len(self.game.players)])
		return opponents

	def get_left_opponent(self):
		counter = 0
		for x in self.game.players:
			if x == self:
				break
			counter += 1

		return self.game.players[(counter + 1) % len(self.game.players)]

	def announce_opponents(self, msg):
		self.game.announce_to(self.get_opponents(), msg)

	def announce_self(self, msg):
		self.game.game_log.append("{} {}{}".format("to:", self.name_string(), msg))
		self.gamelog.append(msg)
		self.write_json(command="announce",msg=msg)

	@gen.coroutine
	def spend_all_money(self):
		to_log = []
		to_discard = []
		treasure_cards = [x for x in self.hand.get_cards_by_type("Treasure", True) if x.get_spend_all()]
		if len(treasure_cards) != 0:
			unique_treasure_titles = set(map(lambda x: x.title, treasure_cards))
			for card_title in unique_treasure_titles:
				card = self.hand.get_card(card_title)
				count = self.hand.get_count(card_title)
				for i in range(0, count):
					card.play(True)
				if len(to_log) != 0:
					to_log.append(",")
				to_discard += self.hand.get_all(card_title)
				to_log.append(str(count))
				to_log.append(card.log_string() if count == 1 else card.log_string(True))
			yield self.discard(list(map(lambda x: x.title, to_discard)), self.played_cards)
			if len(to_log) > 0:
				self.game.announce(self.name_string() + " played " + " ".join(to_log))
				self.update_resources(True)
			self.update_hand()
		else:
			self.update_mode_buy_phase()

	def total_vp(self, returnCards=False):
		total = 0

		# dictionary of vp {"Province" : [<card Province>, 2]}
		vp_dict = {}
		vp_dict["VP tokens"] = ["VP tokens", self.vp]
		total += self.vp
		for card in self.all_cards():
			if "Victory" in card.type or "Curse" in card.type:
				total += card.get_vp()
				if card.title in vp_dict:
					vp_dict[card.title][1] += 1
				else:
					vp_dict[card.title] = [card, 1]
		return total if not returnCards else vp_dict

	def decklist_string(self):
		decklist = cp.CardPile()
		for card in self.all_cards():
			decklist.add(card)
		decklist_str = []
		for card_title in decklist.data.keys():
			decklist_str.append(str(decklist.get_count(card_title)))
			decklist_str.append("-")
			if decklist.get_count(card_title) == 1:
				decklist_str.append(decklist.get_card(card_title).log_string())
			else:
				decklist_str.append(decklist.get_card(card_title).log_string(True))
			decklist_str.append(" ")
		return "".join(decklist_str) + "<br>" + str(len(self.all_cards())) + " cards"

	def name_string(self):
		return "<b>" + html.escape(self.name) + "</b>"

	def get_card_count_in_list(self, card_title, card_list):
		count = 0
		for x in card_list:
			if x.title == card_title:
				count += 1
		return count

	def all_cards(self):
		return self.deck + self.discard_pile + self.played_cards + self.hand.card_array()

	@gen.coroutine
	def resolve_on_buy_effects(self, purchased_card):
		for card in self.played_cards:
			yield gen.maybe_future(card.on_buy_effect(purchased_card))

	@gen.coroutine
	def resolve_on_gain_effects(self, gained_card):
		for card in self.played_cards:
			yield card.on_gain_effect(gained_card)
