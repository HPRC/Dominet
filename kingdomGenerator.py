import card as crd
import base_set as base
import inspect
import random

class kingdomGenerator():
	def __init__(self, game):
		self.game = game
		self.all_cards = []
		for name, obj in inspect.getmembers(base):
			if inspect.isclass(obj):
				self.all_cards.append(obj(game, None))

	def random_kingdom(self):
		kingdom = []
		for i in range(0, 10):
			selected_index = random.randint(0,len(self.all_cards)-1)
			kingdom.append(self.all_cards.pop(selected_index))
		return kingdom
