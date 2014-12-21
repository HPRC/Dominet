from net import GameHandler
import json
import card
import random

class DmClient(GameHandler):
	hand_size = 5

	def base_deck(self):
		deck = []
		for i in range(0,7):
			deck.append(card.Copper(game=self.game, played_by=self))
		for i in range(0,3):
			deck.append(card.Militia(game=self.game, played_by=self))
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
		self.discard_pile = []
		#deck = [bottom, middle, top] 
		self.deck = self.base_deck()
		#dictionary of card title => [card object, count]
		self.hand = {}
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.VP = 0
		self.draw(self.hand_size)
		self.update_hand()

	def update_hand(self):
		self.write_json(command="updateHand", hand=json.dumps(self.hand_array()))

	#override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
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
			self.discard(data["cards"])
		elif (cmd == "endTurn"):
			self.end_turn()
		elif (cmd == "buyCard"):
			self.buy_card(data["card"])
		elif (cmd == "unwait"):
			self.unwait();

	def end_turn(self):
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.draw(self.hand_size)
		self.update_hand()
		self.game.change_turn()

	def buy_card(self, card):
		if (self.buys > 0):
			self.game.announce("<b>" + self.name + "</b> buys " + card)
			self.buys -= 1
			newCard = self.game.kingdom[card][0]
			newCard.played_by = self
			self.discard_pile.append(newCard)
			self.game.kingdom[card][1] -=1
			self.write_json(command="updatePiles", card=card, count=self.game.kingdom[card][1])

	def select_cards(self, num_cards, do_to_select):
		self.write_json(command="updateMode", mode="select", doToSelect=do_to_select, count=num_cards)

	def wait(self, msg):
		self.write_json(command="updateMode", mode="wait")

	def unwait(self):
		if (self.actions > 0):
			default_mode = "action"
		else:
			default_mode = "buy"
		self.game.get_turn_owner().write_json(command="updateMode", mode=default_mode)

	def discard(self, cards):
		for x in cards:
			self.hand[x][1] -= 1
			self.discard_pile.append(self.hand[x][0])
			if (self.hand[x][1] == 0):
				self.hand.pop(x, None)

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
