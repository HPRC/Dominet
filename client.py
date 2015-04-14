import json
import card as crd
import cardpile as cp
import random
import base_set as b
import intrigue_set as intr
import html


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
		print(self.name + ": \033[91m " + str(kwargs) + "\033[0m")
		self.handler.write_json(**kwargs)

	def take_turn(self):
		self.write_json(command="startTurn")

	def exec_commands(self, data):
		cmd = data["command"]

		if self.game is None:
			if cmd == "chat":
				self.handler.chat(data["msg"], self.name)
			return
		# else do game commands
		if cmd == "chat":
			self.game.chat(data["msg"], self.name)

		self.game.log_json_data("\n" + str(json.dumps(data)))


class DmClient(Client):

	def write_json(self, **kwargs):
		if kwargs["command"] == "updateMode":
			# ignore the last_mode if it was a wait for disconnecting
			if not ("msg" in kwargs and "disconnected" in kwargs["msg"]):
				# callback used to resume mode if reconnect
				self.last_mode = kwargs
		Client.write_json(self, **kwargs)

	def base_deck(self):
		deck = []
		for i in range(0, 7):
			deck.append(crd.Copper(game=self.game, played_by=self))
		for i in range(0, 3):
			deck.append(crd.Estate(game=self.game, played_by=self))
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
			self.update_deck_size()
			return drawn
		if len(drawn) == 0:
			return "nothing"
		elif len(drawn) == 1:
			self.update_deck_size()
			return "a card"
		else:
			self.update_deck_size()
			return str(len(drawn)) + " cards"

	# get top card of deck
	def topdeck(self):
		if len(self.deck) == 0:
			self.shuffle_discard_to_deck()
			if len(self.deck) == 0:
				return None
		return self.deck.pop()

	def shuffle_discard_to_deck(self):
		random.shuffle(self.discard_pile)
		self.deck = self.discard_pile + self.deck
		self.discard_pile = []
		self.update_deck_size()
		self.update_discard_size()

	def setup(self):
		self.last_mode = {"command":"updateMode", "mode": "action"}
		self.discard_pile = []
		# deck = [bottom, middle, top]
		self.deck = self.base_deck()
		self.hand = cp.HandPile(self)
		self.played = []
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.draw(self.hand_size)
		self.update_hand()
		# List of players waiting for, callback called after select/gain gets response
		self.waiting = {"on": [], "cb": None}
		self.protection = 0

	def resume_state(self, new_conn):
		new_conn.discard_pile = self.discard_pile
		new_conn.deck = self.deck
		new_conn.hand = self.hand
		new_conn.played = self.played
		new_conn.actions = self.actions
		new_conn.buys = self.buys
		new_conn.balance = self.balance
		new_conn.waiting = self.waiting
		new_conn.last_mode = self.last_mode
		new_conn.protection = self.protection
		for card in self.all_cards():
			card.played_by = new_conn

	def update_hand(self):
		self.write_json(command="updateHand", hand=[x.to_json() for x in self.hand.card_array()])

	# override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		self.write_json(command="updateMode", mode="action")
		self.write_json(command="startTurn", actions=self.actions, buys=self.buys, 
			balance=self.balance)

	# override
	def exec_commands(self, data):
		Client.exec_commands(self, data)
		cmd = data["command"]
		print(self.name + " \033[94m" + json.dumps(data) + "\033[0m")
		if cmd == "ready":
			self.ready = True
			if self.game.players_ready() and self.game.turn_count == 0:
				self.game.turn_count = 1
				self.game.start_game()
			elif self.game.players_ready():
				self.game.load_supplies()
				if self.game.price_modifier != 0:
					self.game.update_all_prices()
				self.resume()
		elif cmd == "play":
			if not data["card"] in self.hand:
				print("Error " + data["card"] + " not in " + self.hand)
			self.hand.play(data["card"])
		elif cmd == "discard":
			self.discard(data["cards"], self.discard_pile)
		elif cmd == "endTurn":
			self.end_turn()
		elif cmd == "buyCard":
			self.buy_card(data["card"])
		elif cmd == "post_selection": 
			self.exec_selected_choice(data["selection"])
		elif cmd == "selectSupply":
			self.update_wait()
			self.exec_selected_choice(data["card"])
		elif cmd == "spendAllMoney":
			self.spend_all_money()
		elif cmd == "returnToLobby":
			self.handler.return_to_lobby()
			self.ready = False
			self.game = None
		elif cmd == "submitBugReport":
			self.game.rename_log_file("logs/flagged_" + str(self.game.START_TIME) + ".txt")
			self.game.flagged = True


	def exec_selected_choice(self, choice):
		self.update_wait()
		# choice(the parameter) to waiting callback is always a list
		if self.waiting["cb"] is not None:
			temp = self.waiting["cb"]
			self.waiting["cb"] = None
			temp(choice)

	def resume(self):
		self.update_hand()
		self.update_resources()
		self.game.update_trash_pile()
		self.write_json(**self.last_mode)
		self.game.announce(self.name_string() + " has reconnected!")
		if self.game.get_turn_owner() == self:
			self.write_json(command="startTurn", actions=self.actions, 
				buys=self.buys, balance=self.balance)

	def end_turn(self):
		#cleanup before game ends
		self.played = [x for x in self.played if x.cleanup()]
		self.discard_pile = self.discard_pile + self.played
		self.played = []

		if self.game.detect_end():
			return
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.draw(self.hand_size)
		if self.game.price_modifier != 0:
			self.game.price_modifier = 0
			self.game.update_all_prices()
		self.update_hand()
		self.update_discard_size()
		self.update_deck_size()
		self.game.change_turn()

	def buy_card(self, card_title):
		if self.buys > 0 and self.game.supply.get_count(card_title) > 0:
			# we instantiate a new card by getting the class from the kingdom instance 
			# and instantiating it
			newCard = type(self.game.card_from_title(card_title))(self.game, self)
			self.game.announce("<b>" + self.name + "</b> buys " + newCard.log_string())
			self.discard_pile.append(newCard)
			self.game.remove_from_supply(card_title)
			self.buys -= 1
			self.balance -= newCard.get_price()

			# try:
			# write on_purchase for Card class, extend it in relevant classes

	def select(self, min_cards, max_cards, select_from, msg, ordered=False):
		if len(select_from) > 0:
			self.write_json(command="updateMode", mode="select", min_cards=min_cards, max_cards=max_cards,
				select_from=select_from, msg=msg, ordered=ordered)
			return True
		else:
			self.update_mode()
			return False

	def wait(self, msg):
		self.write_json(command="updateMode", mode="wait", msg=msg)

	def update_wait(self):
		for i in self.game.players:
			if self in i.waiting["on"]:
				i.waiting["on"].remove(self)
			if len(i.waiting["on"]) == 0:
				i.update_mode()

	def discard(self, cards, pile):
		for x in cards:
			card = self.hand.extract(x)
			if card is not None:
				pile.append(card)
		if pile == self.discard_pile:
			self.update_discard_size()
		elif pile == self.game.trash_pile:
			self.game.update_trash_pile()

	def update_mode(self):
		# if we have no actions or no action cards and no money cards, buy mode
		if (len(self.hand.get_cards_by_type("Action")) == 0 or self.actions == 0) and len(self.hand.get_cards_by_type("Treasure")) == 0:
			self.write_json(command="updateMode", mode="buy")
		else:
			self.write_json(command="updateMode", mode="action" if self.actions > 0 else "buy")

	def update_deck_size(self):
		self.write_json(command="updateDeckSize", size=len(self.deck))

	def update_discard_size(self):
		self.write_json(command="updateDiscardSize", size=len(self.discard_pile))

	def get_card_from_supply(self, card, from_supply=True):
		if self.game.supply.get_count(card) <= 0 and from_supply:
			return
		if from_supply:
			self.game.remove_from_supply(card)
		new_card = type(self.game.card_from_title(card))(self.game, self)
		return new_card

	def gain(self, card, from_supply=True):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			self.game.announce(self.name_string() + " gains " + new_card.log_string())  # TODO perhaps delete to customize gains messages (for attacks etc.)
			self.discard_pile.append(new_card)
			self.update_discard_size()
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + " but it is out of supply.")

	def gain_to_hand(self, card, from_supply=True):
		new_card = self.get_card_from_supply(card, from_supply)
		if new_card is not None:
			self.game.announce(self.name_string() + " gains " + new_card.log_string() + " to their hand.")
			self.hand.add(new_card)
			self.update_hand()
		else:
			self.game.announce(self.name_string() + " tries to gain " + self.game.card_from_title(card).log_string() + "but it is out of supply.")

	def select_from_supply(self, price_limit=None, equal_only=False, type_constraint=None, allow_empty=False, optional=False):
		self.write_json(command="updateMode", mode="selectSupply", price=price_limit, equal_only=equal_only,
			type_constraint=type_constraint, allow_empty=allow_empty, optional=optional)

	def update_resources(self, playedMoney=False):
		if playedMoney:
			self.write_json(command="updateMode", mode="buy")
		self.write_json(command="updateResources", actions=self.actions, buys=self.buys, balance=self.balance)

	def total_deck_size(self):
		return len(self.deck) + len(self.discard_pile) + len(self.played) + len(self.hand)

	def get_opponents(self):
		return [x for x in self.game.players if x != self]

	def get_left_opponent(self):
		counter = 0
		for x in self.game.players:
			if x == self:
				break
			counter += 1

		return self.game.players[(counter + 1) % len(self.game.players)]

	def announce_opponents(self, msg):
		self.game.announce_to(self.get_opponents(), msg)

	def spend_all_money(self):
		to_log = []
		to_discard = []
		treasure_cards = self.hand.get_cards_by_type("Treasure", True)
		unique_treasure_titles = set(map(lambda x: x.title, treasure_cards))
		for card_title in unique_treasure_titles:
			card = self.hand.get_card(card_title)
			count = self.hand.get_count(card_title)
			self.balance += card.value * count
			if len(to_log) != 0:
				to_log.append(",")
			to_discard += self.hand.get_all(card_title)
			to_log.append(str(count))
			to_log.append(card.log_string() if count == 1 else card.log_string(True))
		self.discard(list(map(lambda x: x.title, to_discard)), self.played)
		if len(to_log) > 0:
			self.game.announce(self.name_string() + " played " + " ".join(to_log))
			self.update_resources(True)
		self.update_hand()

	def total_vp(self, returnCards=False):
		total = 0

		# dictionary of vp {"Province" : [<card Province>, 2]}
		vp_dict = {}
		vp_dict["VP"] = self.vp
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
		return "".join(decklist_str)

	def name_string(self):
		return "<b>" + html.escape(self.name) + "</b>"

	def get_card_count_in_list(self, card_title, card_list):
		count = 0
		for x in card_list:
			if x.title == card_title:
				count += 1
		return count

	def all_cards(self):
		return self.deck + self.discard_pile + self.played + self.hand.card_array()

