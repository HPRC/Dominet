"""
This is a wrapper structure to abstract the data structure for hand and supply piles.
"""

import random 


class CardPile():
	def __init__(self):
		# The underlying data is a dictionary with key = cardtitle, value = [card object, count]
		self.data = {}
		self.index = 0

	def add(self, card, count=1):
		if card.title in self.data:
			self.data[card.title] = [card, self.data[card.title][1] + count]
		else:
			self.data[card.title] = [card, count]

	def extract(self, card_title):
		if card_title in self.data:
			self.data[card_title][1] -= 1
			return self.data[card_title][0]
		else:
			print("Error tried to extract card not in cardpile")

	def get_count(self, card_title):
		if card_title not in self.data:
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

	def to_json(self):
		result = []
		for title, lst in self.data.items():
			formatCard = lst[0].to_json()
			formatCard["count"] = lst[1]
			result.append(formatCard)
		return result

	def __iter__(self):
		return self

	def __next__(self):
		self.index += 1
		index_counter = self.index
		for i in self.data:
			if index_counter <= self.data[i][1]:
				return self.data[i][0]
			else:
				index_counter -= self.data[i][1]
		raise StopIteration

	def __len__(self):
		count = 0
		for title, data in self.data.items():
			count += data[1]
		return count

	def __contains__(self, title):
		return title in self.data

	def combine(self, cardPile):
		self.data.update(cardPile.data.copy())

	def pile_contains(self, price=None, cardtype=None):
		price_exists = False
		cardtype_exists = False
		if price:
			for title in self.data:
				if self.data[title][0].price == price:
					price_exists = True
					break

		if cardtype:
			for title in self.data:
				if cardtype in self.data[title][0].type:
					cardtype_exists = True
					break

		return (not price or price_exists) and (not cardtype or cardtype_exists)



class HandPile(CardPile):
	def __init__(self, player):
		# The underlying data is a dictionary with key = cardtitle, value = [card object, count]
		CardPile.__init__(self)
		self.player = player

	def extract(self, card_title):
		if card_title in self.data:
			card = self.data[card_title][0]
			self.data[card_title][1] -= 1
			if self.data[card.title][1] == 0:
				del self.data[card.title]
			return card

	def reveal_string(self):
		h = []
		for title, lst in self.data.items():
			card = lst[0]
			count = lst[1]
			h.append(str(count))
			h.append(card.log_string(True)) if count > 1 else h.append(card.log_string())
		return ", ".join(h)

	# returns list of cards of given type
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

	def auto_select(self, num_options):
		if self.is_homogeneous():
			card = self.card_array()[0]
			return [card for x in range(0, min(len(self.card_array()), num_options))]
		if len(self) == num_options:
			return list(map(lambda x: x.title, self.card_array()))
		return []

	def play(self, card_title):
		self.data[card_title][0].play()