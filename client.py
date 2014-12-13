from net import GameHandler
import json
import card
import random

class DmClient(GameHandler):
	hand_size = 5

	def initialize(self):
		GameHandler.initialize(self)
		self.discard = []
		self.deck = self.base_deck()
		self.hand = []
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.VP = 0

	def base_deck(self):
		deck = []
		for i in range(0,5):
			deck.append(card.Copper(game=self.game, played_by=self))
		deck.append(card.Estate(game=self.game, played_by=self))
		deck.append(card.Estate(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, numCards):
		for i in range(0, numCards):
			self.hand.append(self.deck.pop())

	#override
	def setup(self):
		self.draw(self.hand_size)
		self.write_json(command="initGame", hand=self.hand_json())

	#override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		#self.draw(self.hand_size)
		self.write_json(command="startTurn", actions=self.actions, buys=self.buys, 
			balance=self.balance)

	#override
	def exec_commands(self, data):
		GameHandler.exec_commands(self, data)
		cmd = data["command"]
		print("\033[94m" + json.dumps(data) + "\033[0m")

		if (cmd == "play"):
			pass

	def hand_json(self):
		h = []
		for c in self.hand:
			h.append(
				{"title" : c.title,
				"type" : c.type,
				"description" : c.description
				})
		return json.dumps(h)
