from net import GameHandler
import json
import card
import random

class DmClient(GameHandler):
	hand_size = 5

	#override
	def open(self):
		#resume on player reconnect
		for each_game in self.games:
			for p in each_game.players:
				if (self.name == p.name):
					p.resume_state(self)
					self.game = p.game
					#update game players
					index = self.game.players.index(p)
					self.game.players.pop(index)
					self.game.players.insert(index, self)

					self.update_hand()
					self.write_json(command="kingdomCards", data=self.game.supply_json(self.game.kingdom))
					self.write_json(command="baseCards", data=self.game.supply_json(self.game.base_supply))

					if (each_game.get_turn_owner() == self):
						self.write_json(command="updateMode", mode="action" if self.actions > 0 else "buy")
						self.write_json(command="startTurn", actions=self.actions, 
							buys=self.buys, balance=self.balance)
					self.game.announce(self.name_string() + " has reconnected!")
					return
		GameHandler.open(self)

	def base_deck(self):
		deck = []
		for i in range(0,7):
			deck.append(card.Copper(game=self.game, played_by=self))
		for i in range(0,3):
			deck.append(card.Remodel(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, numCards):
		if (len(self.deck)<5):
			random.shuffle(self.discard_pile)
			self.deck = self.discard_pile + self.deck
			self.discard_pile = []
		for i in range(0, numCards):
			if (len(self.deck) >= 1):
				card = self.deck.pop()
				if (card.title in self.hand):	
					self.hand[card.title] = [card, self.hand[card.title][1] + 1]
				else:
					self.hand[card.title] = [card, 1]

	#override
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
		self.write_json(command="updateHand", hand=json.dumps(self.hand_array()))

	#override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		self.write_json(command="updateMode", mode="action")
		self.write_json(command="startTurn", actions=self.actions, buys=self.buys, 
			balance=self.balance)

	#override
	def exec_commands(self, data):
		GameHandler.exec_commands(self, data)
		cmd = data["command"]
		print("\033[94m" + json.dumps(data) + "\033[0m")

		if (cmd == "play"):
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
		elif (cmd == "unwait"):
			self.unwait(data["selection"], data["card"]);
		elif (cmd == "gain"):
			self.gain(data["card"])

	def end_turn(self):
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.discard_pile = self.discard_pile + self.played
		self.played = []
		self.draw(self.hand_size)
		self.update_hand()
		self.game.change_turn()

	def buy_card(self, card):
		if (self.buys > 0):
			self.game.announce("<b>" + self.name + "</b> buys " + card)
			self.buys -= 1
			newCard = self.game.supply[card][0]
			newCard.played_by = self
			self.discard_pile.append(newCard)
			self.game.remove_from_supply(card)

	def select_cards(self, num_cards, card):
		self.write_json(command="updateMode", mode="select", count=num_cards, card=card)

	def wait(self, msg):
		self.write_json(command="updateMode", mode="wait")

	def unwait(self, selection, card):
		self.game.get_turn_owner().write_json(command="updateMode", mode="action" if self.actions > 0 else "buy")
		tempCard = self.game.supply[card][0]
		tempCard.played_by = self
		tempCard.post_select(selection)

	def discard(self, cards, pile):
		for x in cards:
			self.hand[x][1] -= 1
			pile.append(self.hand[x][0])
			if (self.hand[x][1] == 0):
				self.hand.pop(x, None)

	def gain(self, card):
		self.game.get_turn_owner().write_json(command="updateMode", mode="action" if self.actions > 0 else "buy")
		self.game.announce(self.name_string() + " gains " + card)
		newCard = self.game.supply[card][0]
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

	def name_string(self):
		return "<b>" + self.name + "</b>"
