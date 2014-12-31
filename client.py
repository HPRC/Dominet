import json
import card as crd
import random
import copy

class Client():
	hand_size = 5
	def __init__(self, name, c_id, handler):
		self.name = name
		self.id = c_id
		self.handler = handler

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
			return
		if (cmd == "chat"):
			self.game.chat(data["msg"], self.name)


class DmClient(Client):

	def base_deck(self):
		deck = []
		for i in range(0,7):
			deck.append(crd.Copper(game=self.game, played_by=self))
		for i in range(0,3):
			deck.append(crd.Estate(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, numCards):
		if (len(self.deck)<5):
			self.shuffle_discard_to_deck()
		for i in range(0, numCards):
			if (len(self.deck) >= 1):
				card = self.deck.pop()
				if (card.title in self.hand):	
					self.hand[card.title] = [card, self.hand[card.title][1] + 1]
				else:
					self.hand[card.title] = [card, 1]

	def shuffle_discard_to_deck(self):
		random.shuffle(self.discard_pile)
		self.deck = self.discard_pile + self.deck
		self.discard_pile = []

	def setup(self):
		self.trash_pile = []
		self.discard_pile = []
		#deck = [bottom, middle, top] 
		self.deck = self.base_deck()
		#dictionary of card title => [card object, count]
		self.hand = {}
		self.played = []
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.VP = 0
		self.draw(self.hand_size)
		self.update_hand()

	def resume_state(self, new_conn):
		new_conn.trash_pile = self.trash_pile
		new_conn.discard_pile = self.discard_pile
		new_conn.deck = self.deck
		new_conn.hand = self.hand
		new_conn.played = self.played
		new_conn.actions = self.actions
		new_conn.buys = self.buys
		new_conn.balance = self.balance
		new_conn.VP = self.VP
		for card in self.deck + self.discard_pile + self.trash_pile:
			card.played_by = new_conn
		for title, l in self.hand.items():
			l[0].played_by = new_conn

	def update_hand(self):
		self.write_json(command="updateHand", hand=self.hand_array())

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

		if (cmd == "play"):
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
			self.post_selection(data["selection"], data["card"], data["act_on"]);
		elif (cmd == "gain"):
			self.gain(data["card"])

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
		self.game.change_turn()

	def buy_card(self, card):
		if (self.buys > 0 and self.game.supply[card][1] > 0):
			self.game.announce("<b>" + self.name + "</b> buys " + card)
			# alternative to copy but requires module to have all cards
			# card_class = getattr(crd, card)
			# newCard = card_class(self.game, self)
			newCard = copy.copy(self.game.supply[card][0])
			newCard.played_by = self
			self.discard_pile.append(newCard)
			self.game.remove_from_supply(card)
			self.buys -= 1
			self.balance -= newCard.price
			self.update_resources()

	def select(self, num_needed, card, select_from, msg, act_on=None):
		self.write_json(command="updateMode", mode="select", count=num_needed, card=card, 
			select_from=select_from, msg=msg, act_on=act_on)

	def wait(self, msg):
		self.write_json(command="updateMode", mode="wait", msg=msg)

	def post_selection(self, selection, card, act_on):
		for i in self.game.players:
			i.write_json(command="updateMode", mode="action" if i.actions > 0 else "buy")
		tempCard = self.game.supply[card][0]
		tempCard.played_by = self
		#default act_on is the player who just selected
		if (act_on == None):
			tempCard.post_select(selection)
		else:
			tempCard.post_select(selection, act_on)

	def discard(self, cards, pile):
		for x in cards:
			self.hand[x][1] -= 1
			pile.append(self.hand[x][0])
			if (self.hand[x][1] == 0):
				self.hand.pop(x, None)

	def gain(self, card):
		self.game.get_turn_owner().write_json(command="updateMode", mode="action" if self.actions > 0 else "buy")
		if (self.game.supply[card][1] > 0):
			self.game.announce(self.name_string() + " gains " + card)
			newCard = copy.copy(self.game.supply[card][0])
			newCard.played_by = self
			self.discard_pile.append(newCard)
			self.game.remove_from_supply(card)

	def gain_from_supply(self, price_limit, equal_only):
		self.write_json(command="updateMode", mode="gain", price=price_limit, equal_only=equal_only)

	def update_resources(self):
		self.write_json(command="updateResources", actions=self.actions, buys=self.buys, balance=self.balance)

	def hand_array(self):
		h = []
		for title, data in self.hand.items():
			card = data[0]
			count = data[1]
			for i in range(0, count):
				h.append(card.to_json())
		return h

	def total_vp(self):
		total = 0
		for card in self.deck + self.discard_pile:
			if ("Victory" in card.type):
				total += card.vp
		for title, data in self.hand.items():
			if ("Victory" in data[0].type):
				for i in range(0, data[1]):
					total += data[0].vp
		return total

	def card_list_to_titles(self, lst):
		return list(map(lambda x: x['title'], lst))

	def name_string(self):
		return "<b>" + self.name + "</b>"
