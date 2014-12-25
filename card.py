class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None
		self.price = None

	def play(self):
		self.game.announce(self.played_by.name_string() + " played " + self.title)
		self.played_by.discard([self.title], self.played_by.played)
		if ("Action" in self.type):
			self.played_by.actions -= 1

	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price
		}

	#called after a selection, if played by opponent on me, I use a temp kingdom card with me as owner to resolve effects
	def post_select(self, selection):
		pass

class Money(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Money"
		self.value = None

	def play(self):
		Card.play(self)
		self.played_by.balance += self.value
		self.played_by.update_resources()

	#override
	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price,
			"value": self.value
		}


class Copper(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Copper"
		self.value = 1
		self.price = 0

class Silver(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Silver"
		self.value = 2
		self.price = 3

class Gold(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Gold"
		self.value = 3
		self.price = 6

class Curse(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Curse"
		self.description = "-1 VP"
		self.price = 0
		self.type = "Curse"

	def play(self):
		return

class Estate(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Estate"
		self.description = "+1 VP"
		self.price = 2
		self.type = "Victory"

	def play(self):
		return

class Duchy(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Duchy"
		self.description = "+3 VP"
		self.price = 5
		self.type = "Victory"

	def play(self):
		return

class Province(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Province"
		self.description = "+6 VP"
		self.price = 8
		self.type = "Victory"

	def play(self):
		return

class Cellar(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Cellar"
		self.description = "+1 action, Discard any number of cards, +1 Card per card discarded."
		self.price = 2
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.actions += 1
		self.played_by.select_cards(None, self.title)

	def post_select(self, selection):
		self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.draw(len(selection))
		self.played_by.update_hand()

class Village(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Village"
		self.description = "+1 draw, +2 actions"
		self.price = 3
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.actions += 2
		self.played_by.draw(1)
		self.played_by.update_hand()
		self.played_by.update_resources()

class Woodcutter(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Woodcutter"
		self.description = "$2, +1 Buy"
		self.price = 3
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.buys += 1
		self.played_by.update_resources()

class Militia(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Militia"
		self.description = "+$2, Each other player discards down to 3 cards in hand."
		self.price = 4
		self.type = "Action|Attack"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.update_resources()
		for i in self.game.players:
			if ( i != self.played_by):
				i.select_cards(len(i.hand_array())-3, self.title)
		self.played_by.wait("Waiting for other players to discard")

	def post_select(self, selection):
		self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.update_hand()

class Smithy(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Smithy"
		self.description = "+3 cards"
		self.price = 4
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.draw(3)
		self.played_by.update_hand()
		self.played_by.update_resources()

class Remodel(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Remodel"
		self.description = "Trash a card from your hand, gain a card costing up to 2 more than the trashed card"
		self.price = 4
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.select_cards(1, self.title)
		self.played_by.update_resources()

	def post_select(self, selection):
		self.played_by.discard(selection, self.played_by.trash_pile)
		self.game.announce(self.played_by.name_string() + " trashes " + selection[0])
		card_trashed = self.game.supply[selection[0]][0]
		self.played_by.gain_from_supply(card_trashed.price + 2, False)
		self.played_by.update_hand()

class Festival(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Festival"
		self.description = "+$2, +2 actions, +1 buy"
		self.price = 5
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.actions += 2
		self.played_by.buys += 1
		self.played_by.update_resources()

class Council_Room(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Council Room"
		self.description = "+4 cards, +1 buy. Each other player draws a card"
		self.price = 5
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.draw(4)
		self.played_by.buys += 1
		self.played_by.update_hand()
		self.played_by.update_resources()
		for i in self.game.players:
			if (i != self.played_by):
				i.draw(1)
				i.update_hand()

class Laboratory(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Laboratory"
		self.description = "+2 cards, +1 action"
		self.price = 5
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.draw(2)
		self.played_by.actions += 1
		self.played_by.update_hand()
		self.played_by.update_resources()
