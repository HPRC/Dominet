import sets.card as crd
import sets.base as base
import sets.supply as supply_cards
import sets.intrigue as intrigue
import sets.prosperity as prosperity
import sets.hinterlands as hl
import inspect
import random
import string


class kingdomGenerator():
	avail_sets = [base, intrigue, prosperity, hl]
	kingdom_size = 10

	def __init__(self, game, required_cards=[], excluded_cards=[]):

		self.game = game
		self.avail_cards = {}
		self.required_cards = card_title_to_class_name(required_cards)
		self.excluded_cards = card_title_to_class_name(excluded_cards)
		for each_set in kingdomGenerator.avail_sets:
			self.load_set(each_set)

	def gen_kingdom(self):
		kingdom = []
		# add required cards first
		for x in self.excluded_cards:
			if x in self.avail_cards:
				del self.avail_cards[x]

		for x in self.required_cards:
			if x in self.avail_cards and len(kingdom) < kingdomGenerator.kingdom_size:
				kingdom.append(self.avail_cards[x])
				del self.avail_cards[x]
		# choose random cards to fill out the rest
		if kingdomGenerator.kingdom_size - len(kingdom) > 0:
			kingdom += [self.avail_cards[i] for i in random.sample(list(self.avail_cards), 10 - len(kingdom))]

		return kingdom

	def every_card_kingdom(self):
		kingdom = []
		for x in all_card_titles():
			if x in self.avail_cards:
				kingdom.append(self.avail_cards[x])
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

def all_card_titles():
	titles = []
	for each_set in kingdomGenerator.avail_sets + [supply_cards]:
		for name, obj in inspect.getmembers(each_set):
			if inspect.isclass(obj):
				titles.append(obj(None, None).title)
	return titles	

