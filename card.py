class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None
		self.price = None

	def play(self):
		self.game.announce("<b>" + self.played_by.name + "</b> played " + self.title)
		if ("Action" in self.type):
			self.played_by.actions -= 1

	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price
		}

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
		self.description = "$2, Each other player discards down to 3 cards in hand."
		self.price = 4
		self.type = "Action|Attack"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.update_resources()
		for i in self.game.players:
			if ( i != self.played_by):
				i.select_cards(len(i.hand_array())-3, "discard")
		self.played_by.wait("Waiting for other players to discard")





