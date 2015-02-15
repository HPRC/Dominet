"""
This is a wrapper structure to abstract the datastructure for hand, supply, deck & discard piles.
"""

import random 

class CardPile():
	def __init__(self):
		# The underlying data is a dictionary with key = cardtitle, value = [card object, count]
		self.data = {}

	def add(self, card):
		if (card.title in self.data):	
			self.data[card.title] = [card, self.data[card.title][1] + 1]
		else:
			self.data[card.title] = [card, 1]

	def extract(self, card_title):
		if (card_title in self.data):
			self.data[card_title][1] -= 1
			return self.data[card_title][0]
		else:
			print("Error tried to extract card not in cardpile")

	def get_count(self, card_title):
		if not card_title in self.data:
			return 0
		return self.data[card_title][1]

	def get_card(self, card_title):
		return self.data[card_title][0]

	def card_array(self):
		arr = []
		for title, lst in self.data.items():
			card = lst[0]
			count = lst[1]
			for i in range(0, count):
				arr.append(card)
		return arr

class HandPile(CardPile):
	def __init__(self, player):
		# The underlying data is a dictionary with key = cardtitle, value = [card object, count]
		CardPile.__init__(self)
		self.player = player

	def extract(self, card_title):
		if (card_title in self.data):
			card = self.data[card_title][0]
			self.data[card_title][1] -= 1
			if (self.data[card.title][1] == 0):
				del self.data[card.title]
			return card


	def has(self, card_title):
		return card_title in self.data

	def reveal_string(self):
		h = []
		for title, lst in self.data.items():
			card = lst[0]
			count = lst[1]
			h.append(str(count))
			h.append(card.log_string(True)) if count > 1 else h.append(card.log_string())
		return ", ".join(h)

	#returns list of cards of given type
	def get_cards_by_type(self, ctype, include_subtypes=True):
		results = []
		for card in self.card_array():
			if include_subtypes:
				if ctype in card.type:
					results.append(card)
			else:
				if ctype == card.type:
					results.append(card)
		return results

	def is_homogeneous(self):
		return len(self.data) == 1

	def size(self):
		return len(self.card_array())

	def auto_select(self, num_options):
		if self.is_homogeneous():
			card = self.card_array()[0]
			return [card for x in range(0, num_options)]
		if self.size() == num_options:
			return list(map(lambda x: x.title, self.card_array()))
		print("Error auto_select returned []")
		return []

	def play(self, card_title):
		self.data[card_title][0].play()

class ListPile():
	def __init__(self, player):
		# The underlying data is a list of card objects
		# order of ListPile is [bottom, middle, top] 
		self.data = []

	def add(self, card):
		self.data.append(card)

	def get_cards_from_top(self, num_cards):
		return self.data[-num_cards:]

	def shuffle(self):
		random.shuffle(self.data)

	def size(self):
		return len(self.data)


