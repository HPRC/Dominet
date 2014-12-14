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
		deck.append(card.Estate(game=self.game, played_by=self))
		deck.append(card.Estate(game=self.game, played_by=self))
		random.shuffle(deck)
		return deck

	def draw(self, numCards):
		for i in range(0, numCards):
			card = self.deck.pop()
			if (card.title in self.hand):	
				self.hand[card.title] = [card, self.hand[card.title][1] + 1]
			else:
				self.hand[card.title] = [card, 1]

	#override
	def setup(self):
		self.discard = []
		self.deck = self.base_deck()
		#dictionary of card title => [card object, count]
		self.hand = {}
		self.actions = 0
		self.buys = 0
		self.balance = 0
		self.VP = 0
		self.draw(self.hand_size)
		self.write_json(command="initGame", hand=self.hand_json())

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
				handtuple[1] -= 1
				handtuple[0].play()

	def hand_json(self):
		h = []
		for title, data in self.hand.items():
			card = data[0]
			count = data[1]
			for i in range(0, count):
				h.append(
					{"title" : card.title,
					"type" : card.type,
					"description" : card.description
					})
		return json.dumps(h)
