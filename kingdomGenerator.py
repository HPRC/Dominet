import card as crd
import base_set as base
import intrigue_set as intrigue
import inspect
import random

class kingdomGenerator():
	def __init__(self, game):
		self.game = game
		self.avail_cards = []
		self.load_set(base)
		self.load_set(intrigue)

	def random_kingdom(self):
		kingdom = []
		for i in range(0, 10):
			selected_index = random.randint(0,len(self.avail_cards)-1)
			kingdom.append(self.avail_cards.pop(selected_index))
		return kingdom

	def load_set(self, card_set):
		for name, obj in inspect.getmembers(card_set):
			if inspect.isclass(obj):
				self.avail_cards.append(obj(self.game, None))


def all_cards(game):
	all_cards = []
	for name, obj in inspect.getmembers(base):
		if inspect.isclass(obj):
			all_cards.append(obj(game, None))
	for name, obj in inspect.getmembers(crd):
		if inspect.isclass(obj):
			all_cards.append(obj(game, None))
	return all_cards