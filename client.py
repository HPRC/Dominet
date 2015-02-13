import json
import card as crd
import random
import copy
import base_set as b
import cgi

class Client():
	hand_size = 5
	def __init__(self, name, c_id, handler):
		self.name = name
		self.id = c_id
		self.handler = handler
		self.game = None
		self.ready = False

	#called before players take their turns
	def setup(self):
		pass

	def write_json(self, **kwargs):
		self.handler.write_json(**kwargs)

	def take_turn(self):
		self.write_json(command="startTurn")

	def exec_commands(self, data):
		cmd = data["command"]

		if self.game == None:
			if (cmd == "chat"):
				self.handler.chat(data["msg"], self.name)
			return
		#else do game commands
		if (cmd == "chat"):
			self.game.chat(data["msg"], self.name)

class DmClient(Client):

	def write_json(self, **kwargs):
		if kwargs["command"] == "updateMode":
			#callback used to resume mode if reconnect
			self.last_mode = kwargs
		Client.write_json(self, **kwargs)

	def base_deck(self):
		deck = []
		for i in range(0,7):
			deck.append(crd.Copper(game=self.game, played_by=self))
		for i in range(0,3):
			deck.append(crd.Estate(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, numCards):
		num_drawn = 0
		if (len(self.deck)<numCards):
			self.shuffle_discard_to_deck()
		for i in range(0, numCards):
			if (len(self.deck) >= 1):
				num_drawn += 1
				card = self.deck.pop()
				if (card.title in self.hand):	
					self.hand[card.title] = [card, self.hand[card.title][1] + 1]
				else:
					self.hand[card.title] = [card, 1]
		if num_drawn == 0:
			return "nothing"
		elif num_drawn == 1:
			self.update_deck_size()
			return "a card"
		else:
			self.update_deck_size()
			return str(num_drawn) + " cards"

	#get top card of deck
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
		#deck = [bottom, middle, top] 
		self.deck = self.base_deck()
		#dictionary of card title => [card object, count]
		self.hand = {}
		self.played = []
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.draw(self.hand_size)
		self.update_hand()
		#List of players waiting for, callback called after select/gain gets response
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
		for card in self.deck + self.discard_pile + self.played:
			card.played_by = new_conn
		for title, l in self.hand.items():
			l[0].played_by = new_conn

	def update_hand(self):
		self.write_json(command="updateHand", hand=[x.to_json() for x in self.hand_array()])

	#override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		self.write_json(command="updateMode", mode="action")
		self.write_json(command="startTurn", actions=self.actions, buys=self.buys, 
			balance=self.balance)

	#override
	def exec_commands(self, data):
		Client.exec_commands(self, data)
		cmd = data["command"]
		print("\033[94m" + json.dumps(data) + "\033[0m")
		if (cmd == "ready"):
			self.ready = True
			if (self.game.players_ready() and self.game.turn_count == 0):
				self.game.turn_count = 1
				self.game.start_game()
			elif (self.game.players_ready()):
				self.game.load_supplies()
				self.resume()
		elif (cmd == "play"):
			if (data["card"] not in self.hand):
				print(self.hand)
			handtuple = self.hand[data["card"]]
			if (handtuple[1] - 1 < 0 ):
				print ("error, tried to play a card no longer in hand")
			else:
				handtuple[0].play()
		elif (cmd == "discard"):
			self.discard(data["cards"], self.discard_pile)
		elif (cmd == "endTurn"):
			self.end_turn()
		elif (cmd == "buyCard"):
			self.buy_card(data["card"])
		elif (cmd == "post_selection"):
			self.update_wait()
			#parameter to waiting callback here is a list
			if (self.waiting["cb"] != None):
				self.waiting["cb"](data["selection"])
		elif (cmd == "gain"):
			self.update_wait()
			#parameter to waiting callback here is a string
			if (self.waiting["cb"] != None):
				self.waiting["cb"](data["card"])
		elif (cmd == "spendAllMoney"):
			self.spend_all_money()
		elif (cmd == "returnToLobby"):
			self.handler.return_to_lobby()
			self.ready = False
			self.game = None

	def resume(self):
		self.update_hand()
		self.update_resources()
		self.game.update_trash_pile()
		if (self.game.get_turn_owner() == self):
			self.write_json(**self.last_mode)
			self.write_json(command="startTurn", actions=self.actions, 
			buys=self.buys, balance=self.balance)
		for i in self.get_opponents():
			i.update_mode()
		self.game.announce(self.name_string() + " has reconnected!")

	def end_turn(self):
		if self.game.detect_end():
			return
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.discard_pile = self.discard_pile + self.played
		self.played = []
		self.draw(self.hand_size)
		self.update_hand()
		self.update_discard_size()
		self.update_deck_size()
		self.game.change_turn()

	def buy_card(self, card):
		if (self.buys > 0 and self.game.supply[card][1] > 0):
			# alternative to copy but requires module to have all cards
			# card_class = getattr(crd, card)
			# newCard = card_class(self.game, self)
			newCard = copy.copy(self.game.card_from_title(card))
			newCard.played_by = self
			self.game.announce("<b>" + self.name + "</b> buys " + newCard.log_string())
			self.discard_pile.append(newCard)
			self.game.remove_from_supply(card)
			self.buys -= 1
			self.balance -= newCard.price
			self.update_resources()

	def select(self, min_cards, max_cards, select_from, msg):
		if (len(select_from) > 0):
			self.write_json(command="updateMode", mode="select", min_cards=min_cards, max_cards=max_cards,
				select_from=select_from, msg=msg)
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
			self.hand[x][1] -= 1
			pile.append(self.hand[x][0])
			if (self.hand[x][1] == 0):
				del self.hand[x]
		if (pile == self.discard_pile):
			self.update_discard_size()
		elif (pile == self.game.trash_pile):
			self.game.update_trash_pile()

	def insert_card_in_hand(self, card):
		if (card.title in self.hand):
			self.hand[card.title][1] += 1
		else:
			self.hand[card.title] = [card, 1]

	def update_mode(self):
		self.write_json(command="updateMode", mode="action" if self.actions > 0 else "buy")

	def update_deck_size(self):
		self.write_json(command="updateDeckSize", size=len(self.deck))

	def update_discard_size(self):
		self.write_json(command="updateDiscardSize", size=len(self.discard_pile))

	def gain(self, card, from_supply = True):
		self.game.get_turn_owner().update_mode()
		if (self.game.supply[card][1] <= 0 and from_supply):
			return
		if (from_supply):
			self.game.remove_from_supply(card)
		newCard = copy.copy(self.game.card_from_title(card))
		newCard.played_by = self
		self.game.announce(self.name_string() + " gains " + newCard.log_string())
		self.discard_pile.append(newCard)
		self.update_discard_size()

	def gain_from_supply(self, price_limit, equal_only, type_constraint = None):
		self.write_json(command="updateMode", mode="gain", price=price_limit, equal_only=equal_only, 
			type_constraint = type_constraint)

	def update_resources(self, playedMoney = False):
		if (playedMoney):
			self.write_json(command="updateMode", mode="buy")
		self.write_json(command="updateResources", actions=self.actions, buys=self.buys, balance=self.balance)

	def hand_array(self):
		h = []
		for title, data in self.hand.items():
			card = data[0]
			count = data[1]
			for i in range(0, count):
				h.append(card)
		return h

	def hand_string(self):
		h = []
		for title, data in self.hand.items():
			card = data[0]
			count = data[1]
			h.append(str(count))
			h.append(card.log_string(True)) if count > 1 else h.append(card.log_string())
		return " ".join(h)

	def total_deck_size(self):
		return len(self.deck) + len(self.discard_pile) + len(self.played) + len(self.hand_array())

	def get_opponents(self):
		return [x for x in self.game.players if x != self]

	def announce_opponents(self, msg):
		self.game.announce_to(self.get_opponents(), msg)

	def spend_all_money(self):
		to_log = []
		to_discard = {}
		for title, data in self.hand.items():
			if (data[0].type == "Treasure"):
				for count in range(0, data[1]):
					self.balance += data[0].value
				if (len(to_log) != 0):
					to_log.append(",")
				to_discard[data[0].title] = data[1]
				to_log.append(str(data[1]))
				to_log.append(data[0].log_string() if data[1] == 1 else data[0].log_string(True))
		for title, count in to_discard.items():
			for i in range(0, count):
				self.discard([title], self.played)
		if (len(to_log) > 0):
			self.game.announce(self.name_string() + " played " + " ".join(to_log))
			self.update_resources(True)
		self.update_hand()

	def total_vp(self, returnCards = False):
		total = 0
		# dictionary of vp {"Province" : [<card Province>, 2]}
		vp_dict = {}
		for card in self.deck + self.discard_pile + self.played:
			if ("Victory" in card.type or "Curse" in card.type):
				total += card.get_vp()
				if card.title in vp_dict:
					vp_dict[card.title][1] += 1
				else:
					vp_dict[card.title] = [card, 1]
		for title, data in self.hand.items():
			if ("Victory" in data[0].type or "Curse" in data[0].type):
				total += (data[0].get_vp() * data[1])
				if data[0].title in vp_dict:
					vp_dict[data[0].title][1] += data[1]
				else:
				 	vp_dict[data[0].title] = [data[0], data[1]]
		return total if not returnCards else vp_dict

	def decklist_string(self):
		decklist = {}
		for card_title in crd.card_list_to_titles(self.deck + self.discard_pile + self.played):
			if card_title in decklist:
				decklist[card_title] += 1  
			else:
				decklist[card_title] = 1
		for card_title in crd.card_list_to_titles(self.hand_array()):
			if card_title in decklist:
				decklist[card_title] += 1
			else:
				decklist[card_title] = 1
		decklist_str = []
		for card_title, count in decklist.items():
			decklist_str.append(str(count))
			decklist_str.append("-")
			if count == 1:
				decklist_str.append(self.game.supply[card_title][0].log_string())
			else:
				decklist_str.append(self.game.supply[card_title][0].log_string(True))
			decklist_str.append(" ")
		return "".join(decklist_str)


	def name_string(self):
		return "<b>" + cgi.escape(self.name) + "</b>"
