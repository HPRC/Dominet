class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None
		self.price = None

	def play(self):
		self.game.announce(self.played_by.name_string() + " played " + self.log_string())
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

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", self.title, "s</span>" if plural else "</span>"])

class Money(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Money"
		self.value = None

	def play(self):
		Card.play(self)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

	#override
	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price,
			"value": self.value
		}

	def log_string(self, plural=False):
		return "".join(["<span class='label label-warning'>", self.title, "s</span>" if plural else "</span>"])

class AttackCard(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Action|Attack"
		self.reactions = 0

	#called after reaction card finishes
	def reacted(self):
		self.reactions -=1
		if self.reactions == 0:
			self.attack()

	def check_reactions(self, targets):
		for i in targets:
			for name, card in i.hand.items():
				if (card[0].type == "Action|Reaction" and card[0].trigger == "Attack"):
					self.reactions += 1
					card[0].react(self.reacted)
					self.played_by.wait("Waiting for " + i.name + " to react")
		if not self.reactions:
			self.attack()

	def attack(self):
		pass

	def log_string(self, plural=False):
		return "".join(["<span class='label label-danger'>", self.title, "s</span>" if plural else "</span>"])

class Copper(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Copper"
		self.value = 1
		self.price = 0
		self.description = "+$1"

class Silver(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Silver"
		self.value = 2
		self.price = 3
		self.description = "+$2"

class Gold(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Gold"
		self.value = 3
		self.price = 6
		self.description = "+$3"

class Curse(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Curse"
		self.description = "-1 VP"
		self.price = 0
		self.vp = -1
		self.type = "Curse"

	def play(self):
		return

class Estate(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Estate"
		self.description = "+1 VP"
		self.price = 2
		self.vp = 1
		self.type = "Victory"

	def play(self):
		return
		
	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", self.title, "s</span>" if plural else "</span>"])

class Duchy(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Duchy"
		self.description = "+3 VP"
		self.price = 5
		self.vp = 3
		self.type = "Victory"

	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", self.title, "s</span>" if plural else "</span>"])

class Province(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Province"
		self.description = "+6 VP"
		self.price = 8
		self.vp = 6
		self.type = "Victory"

	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", self.title, "s</span>" if plural else "</span>"])

class Cellar(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Cellar"
		self.description = "+1 action\n Discard any number of cards, +1 Card per card discarded."
		self.price = 2
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.actions += 1
		self.played_by.select(None, self.title, 
			self.played_by.card_list_to_titles(self.played_by.hand_array()), "select cards to discard")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.draw(len(selection))
		self.played_by.update_hand()


class Moat(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Moat"
		self.description = "+2 cards\n Whenever another player plays an Attack card, you may reveal this card from\
		your hand, if you do, you are unaffected by the Attack."
		self.price = 2
		self.type = "Action|Reaction"
		self.trigger = "Attack"

	def play(self):
		Card.play(self)
		self.played_by.draw(2)
		self.played_by.update_resources()
		self.played_by.update_hand()
		self.played_by.update_mode()

	def react(self, react_to_callback):
		self.played_by.select(1, self.title, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to prevent attack?")

		def new_cb(selection):
			self.post_select(selection)
			react_to_callback()

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = new_cb

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		if (selection[0] == "Reveal"):
			self.game.announce(self.played_by.name_string() + " reveals " + self.title)


class Village(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Village"
		self.description = "+1 draw\n +2 actions"
		self.price = 3
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.actions += 2
		self.played_by.draw(1)
		self.game.announce("-- gaining 2 actions and drawing a card")
		self.played_by.update_hand()
		self.played_by.update_resources()

class Woodcutter(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Woodcutter"
		self.description = "$2\n +1 Buy"
		self.price = 3
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining $2 and 1 buy")
		self.played_by.update_resources()
		self.played_by.update_mode()

class Spy(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Spy"
		self.description = "+1 card\n +1 action\n Each player (including you) reveals the top card of his deck and either discards it or puts it back, your choice"
		self.price = 4

	def play(self):
		Card.play(self)
		self.played_by.actions += 1
		self.played_by.draw(1)
		self.game.announce("-- getting +1 action, +1 card")
		self.played_by.update_resources()
		self.played_by.update_hand()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		self.fire(self.played_by)

	def fire(self, player):
		if (len(player.deck) < 1):
			player.shuffle_discard_to_deck()
		revealed_card = player.deck[-1]
		self.played_by.select(1, self.title, ["discard", "keep"],  
			player.name + " revealed " + revealed_card.title)

		def post_select_on(selection, player=player):
			self.post_select(selection, player)

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = post_select_on

	def post_select(self, selection, act_on):
		if (selection[0] == "discard"):
			card = act_on.deck.pop()
			act_on.discard_pile.append(card)
			self.game.announce(self.played_by.name_string() + " discards " + card.log_string() + " from " + 
				act_on.name_string() + "'s deck")
		else:
			card = act_on.deck[-1]
			self.game.announce(self.played_by.name_string() + " leaves " + card.log_string() + " on " + 
				act_on.name_string() + "'s deck")
		next_player_index = (self.game.players.index(act_on) + 1) % len(self.game.players)
		if (self.game.players[next_player_index] != self.played_by):
			self.fire(self.game.players[next_player_index])

class Militia(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Militia"
		self.description = "+$2\n Each other player discards down to 3 cards in hand."
		self.price = 4
		self.type = "Action|Attack"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.update_resources()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		for i in self.game.players:
			if ( i != self.played_by):
				i.select(len(i.hand_array())-3, self.title, i.card_list_to_titles(i.hand_array()),
				 "select 2 cards to discard")
			
				def post_select_on(selection, i=i):
					self.post_select(selection, i)

				i.waiting["on"].append(i)
				i.waiting["cb"] = post_select_on
				self.played_by.waiting["on"].append(i)
		self.played_by.wait("Waiting for other players to discard")

	def post_select(self, selection, act_on):
		act_on.discard(selection, act_on.discard_pile)
		act_on.update_hand()

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
		self.game.announce("-- drawing 3 cards")
		self.played_by.update_hand()
		self.played_by.update_resources()
		self.played_by.update_mode()

class Moneylender(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Moneylender"
		self.description = "trash a copper from your hand, if you do +$3"
		self.price = 4
		self.type = "Action"

	def play(self):
		Card.play(self)
		if ("Copper" in self.played_by.hand.keys()):
			self.played_by.discard(["Copper"], self.played_by.trash_pile)
			self.played_by.balance += 3
			self.game.announce("-- trashing a copper and gaining $3")
		else:
			self.game.announce("-- but has no copper to trash")
		self.played_by.update_hand()
		self.played_by.update_resources()
		self.played_by.update_mode()

class Remodel(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Remodel"
		self.description = "Trash a card from your hand, gain a card costing up to 2 more than the trashed card"
		self.price = 4
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.select(1, self.title, self.played_by.card_list_to_titles(self.played_by.hand_array()),
		 "select card to remodel")
		self.played_by.update_resources()
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

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
		self.description = "+$2\n +2 actions\n +1 buy"
		self.price = 5
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.balance += 2
		self.played_by.actions += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining 2 actions, 1 buy and $2")
		self.played_by.update_resources()

class Council_Room(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Council Room"
		self.description = "+4 cards\n +1 buy\n Each other player draws a card"
		self.price = 5
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.draw(4)
		self.played_by.buys += 1
		self.played_by.update_hand()
		self.played_by.update_resources()
		self.game.announce("-- drawing 4 cards and getting +1 buy")
		self.game.announce("-- each other player draws a card")
		for i in self.game.players:
			if (i != self.played_by):
				i.draw(1)
				i.update_hand()
		self.played_by.update_mode()

class Laboratory(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Laboratory"
		self.description = "+2 cards\n +1 action"
		self.price = 5
		self.type = "Action"

	def play(self):
		Card.play(self)
		self.played_by.draw(2)
		self.played_by.actions += 1
		self.game.announce("-- drawing 2 cards and gaining +1 action")
		self.played_by.update_hand()
		self.played_by.update_resources()

class Witch(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Witch"
		self.description = "+2 cards\n Each other player gains a curse card"
		self.price = 5

	def play(self):
		Card.play(self)
		self.played_by.draw(2)
		self.game.announce("-- drawing 2 cards")
		self.played_by.update_hand()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		for i in self.game.players:
			if (i != self.played_by):
				i.gain("Curse")
		self.played_by.update_mode()
