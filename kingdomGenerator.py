import card as crd
import base_set as base
import intrigue_set as intrigue
import prosperity_set as prosperity
import inspect
import random
import string


class kingdomGenerator():
	def __init__(self, game, required_cards=[], excluded_cards=[]):
		self.game = game
		self.avail_cards = {}
		self.required_cards = card_title_to_class_name(required_cards)
		self.excluded_cards = card_title_to_class_name(excluded_cards)
		self.load_set(base)
		self.load_set(intrigue)
		self.load_set(prosperity)

	def gen_kingdom(self):
		kingdom = []
		# add required cards first
		for x in self.excluded_cards:
			if x in self.avail_cards:
				del self.avail_cards[x]

		for x in self.required_cards:
			if x in self.avail_cards:
				kingdom.append(self.avail_cards[x])
				del self.avail_cards[x]
		# choose random cards to fill out the rest
		if 10 - len(kingdom) > 0:
			kingdom += [self.avail_cards[i] for i in random.sample(list(self.avail_cards), 10 - len(kingdom))]

		return kingdom

	def load_set(self, card_set):
		for name, obj in inspect.getmembers(card_set):
			if inspect.isclass(obj):
				card = obj(self.game, None)
				self.avail_cards[card.title] = card


# replaces strips spaces to single space and changes to camelcase
def card_title_to_class_name(lst):
	result = []
	for x in lst:
		x = " ".join("".join([w[0].upper(), w[1:].lower()]) for w in x.split())
		result.append(x)
	return result 


def all_cards(game):
	all_cards = []
	for name, obj in inspect.getmembers(base):
		if inspect.isclass(obj):
			all_cards.append(obj(game, None))
	for name, obj in inspect.getmembers(crd):
		if inspect.isclass(obj):
			if obj.__name__ != "Card":
				all_cards.append(obj(game, None))
	for name, obj in inspect.getmembers(intrigue):
		if inspect.isclass(obj):
			all_cards.append(obj(game, None))
	for name, obj in inspect.getmembers(prosperity):
		if inspect.isclass(obj):
			all_cards.append(obj(game, None))
	return all_cards