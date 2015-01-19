class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None
		self.price = None
		self.done = lambda : None

	def play(self, skip=False):
		if not skip:
			self.game.announce(self.played_by.name_string() + " played " + self.log_string())
			self.played_by.discard([self.title], self.played_by.played)
			if ("Action" in self.type):
				self.played_by.actions -= 1

	#called at the end of a card's resolution
	def on_finished(self, modified_hand = True, modified_resources = True):
		if modified_resources:
			self.played_by.update_resources()
		if modified_hand:
			self.played_by.update_hand()
		self.played_by.update_mode()
		self.done()

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

	def play(self, skip=False):
		Card.play(self, skip)
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

	def is_blocked(self, target):
		if (target.protection == 0):
			return False
		else:
			target.protection -= 1
			self.game.announce(target.name_string() + " is unaffected by the attack")
			return True

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

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.actions += 1
		self.played_by.select(None, 
			self.played_by.card_list_to_titles(self.played_by.hand_array()), "select cards to discard")
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		self.played_by.discard(selection, self.played_by.discard_pile)
		self.played_by.draw(len(selection))
		Card.on_finished(self)


class Moat(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Moat"
		self.description = "+2 cards\n Whenever another player plays an Attack card, you may reveal this card from\
		your hand, if you do, you are unaffected by the Attack."
		self.price = 2
		self.type = "Action|Reaction"
		self.trigger = "Attack"

	def play(self, skip=False):
		Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.game.announce(" -- drawing " + drawn)
		Card.on_finished(self)

	def react(self, react_to_callback):
		self.played_by.select(1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to prevent attack?")

		def new_cb(selection):
			self.post_select(selection)
			react_to_callback()

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = new_cb

	def post_select(self, selection):
		self.played_by.waiting["cb"] = None
		if (selection[0] == "Reveal"):
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			self.played_by.protection += 1

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])

class Village(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Village"
		self.description = "+1 draw\n +2 actions"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.actions += 2
		drawn = self.played_by.draw(1)
		self.game.announce("-- gaining 2 actions and drawing " + drawn)
		Card.on_finished(self)

class Woodcutter(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Woodcutter"
		self.description = "$2\n +1 Buy"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining $2 and 1 buy")
		Card.on_finished(self)

class Workshop(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Workshop"
		self.description = "Gain a card costing up to $4"
		self.price = 3
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.gain_from_supply(4, False)

	def post_gain(self, card_title):
		self.played_by.gain(card_title)
		Card.on_finished(self, False, False)

class Bureaucrat(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Bureaucrat"
		self.description = "Gain a Silver, put it on top of your deck. Each other player reveals a Victory card\
			and puts it on his deck or reveals a hand with no Victory cards."
		self.price = 4

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.gain("Silver")
		self.played_by.update_resources()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		for i in self.game.get_opponents(self.played_by):
			if not AttackCard.is_blocked(self, i):
				i_victory_cards = []
				for title, data in i.hand.items():
					if "Victory" in data[0].type:
						i_victory_cards.append(data[0])
				if len(i_victory_cards) == 0:
					self.game.announce(i.name_string() + " has no Victory cards & reveals " + i.hand_string())
					self.done()
				elif len(i_victory_cards) == 1:
					self.game.announce(i.name_string() + " puts " + i_victory_cards[0].log_string() + " back on top of the deck")
					i.discard([i_victory_cards[0].title], i.deck)
					i.update_hand()
					self.done()
				else:
					i.select(1, i.card_list_to_titles(i_victory_cards), 
						"select 2 cards to discard")

					def post_select_on(selection, i=i):
						self.post_select(selection, i)

					i.waiting["on"].append(i)
					i.waiting["cb"] = post_select_on
					self.played_by.waiting["on"].append(i)
					self.played_by.wait("Waiting for other players to choose a Victory card to put back")

	def post_select(self, selection, act_on):
		act_on.discard(selection, act_on.deck)
		self.game.announce(act_on.name_string() + " puts " + self.game.supply[selection[0]][0].log_string() + " back on top of the deck")
		act_on.update_hand()
		Card.on_finished(self, False, False)

class Spy(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Spy"
		self.description = "+1 card\n +1 action\n Each player (including you) reveals the top card of his deck and either discards it or puts it back, your choice"
		self.price = 4

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.actions += 1
		drawn = self.played_by.draw(1)
		self.game.announce("-- getting +1 action and drawing " + drawn)
		self.played_by.update_resources()
		self.played_by.update_hand()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		self.fire(self.played_by)

	def fire(self, player):
		if not AttackCard.is_blocked(self, player):
			if (len(player.deck) < 1):
				player.shuffle_discard_to_deck()
				if (len(player.deck) <1):
					self.game.announce(player.name_string() + " has no cards to Spy.")
					self.get_next(player)
					return
			revealed_card = player.deck[-1]
			self.played_by.select(1, ["discard", "keep"],  
				player.name + " revealed " + revealed_card.title)

			def post_select_on(selection, player=player):
				self.post_select(selection, player)

			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = post_select_on
		else:
			self.get_next(player)

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
		self.get_next(act_on)

	def get_next(self, act_on):
		next_player_index = (self.game.players.index(act_on) + 1) % len(self.game.players)
		if (self.game.players[next_player_index] != self.played_by):
			self.fire(self.game.players[next_player_index])
		else:
			print(self.done)
			Card.on_finished(self, False, False)

class Militia(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Militia"
		self.description = "+$2\n Each other player discards down to 3 cards in hand."
		self.price = 4
		self.type = "Action|Attack"

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.update_resources()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		for i in self.game.get_opponents(self.played_by):
			if not AttackCard.is_blocked(self, i):
				i.select(len(i.hand_array())-3, i.card_list_to_titles(i.hand_array()),
				 "select 2 cards to discard")
			
				def post_select_on(selection, i=i):
					self.post_select(selection, i)

				i.waiting["on"].append(i)
				i.waiting["cb"] = post_select_on
				self.played_by.waiting["on"].append(i)
				self.played_by.wait("Waiting for other players to discard")

	def post_select(self, selection, act_on):
		act_on.discard(selection, act_on.discard_pile)
		Card.on_finished(self, False, False)

class Smithy(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Smithy"
		self.description = "+3 cards"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		drawn = self.played_by.draw(3)
		self.game.announce("-- drawing " + drawn)
		Card.on_finished(self)

class Moneylender(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Moneylender"
		self.description = "trash a copper from your hand, if you do +$3"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		if ("Copper" in self.played_by.hand.keys()):
			self.played_by.discard(["Copper"], self.played_by.trash_pile)
			self.played_by.balance += 3
			self.game.announce("-- trashing a copper and gaining $3")
		else:
			self.game.announce("-- but has no copper to trash")
		Card.on_finished(self)

class Remodel(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Remodel"
		self.description = "Trash a card from your hand, gain a card costing up to 2 more than the trashed card"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.select(1, self.played_by.card_list_to_titles(self.played_by.hand_array()),
		 "select card to remodel")
		self.played_by.update_resources()
		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_select

	def post_select(self, selection):
		self.played_by.discard(selection, self.played_by.trash_pile)
		self.game.announce(self.played_by.name_string() + " trashes " + selection[0])
		card_trashed = self.game.supply[selection[0]][0]
		self.played_by.gain_from_supply(card_trashed.price + 2, False)

		self.played_by.waiting["on"].append(self.played_by)
		self.played_by.waiting["cb"] = self.post_gain
		self.played_by.update_hand()

	def post_gain(self, card_title):
		self.played_by.gain(card_title)
		Card.on_finished(self, False, False)

class Throne_Room(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Throne Room"
		self.description = "Choose an action card from your hand. Play it twice."
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		action_cards = [x for x in self.played_by.hand_array() if "Action" in x.type]
		if not self.played_by.select(1, self.played_by.card_list_to_titles(action_cards),
		 "select card for Throne Room"):
			self.done = lambda : None
		else:
			self.played_by.waiting["on"].append(self.played_by)
			self.played_by.waiting["cb"] = self.post_select
		self.played_by.update_resources()

	def post_select(self, selection):
		selected_card = self.played_by.hand[selection[0]][0]
		throne_room_str = self.played_by.name_string() + " " + self.log_string(True) + " " + selected_card.log_string()
		def second_play(card=selected_card):

			def final_done(card=card):
				#after the second play of card is finished, throne room is done
				card.done = lambda : None
				Card.on_finished(self, False, False)

			card.game.announce(throne_room_str)
			card.done = final_done
			card.play(True)
			card.played_by.update_resources()
		selected_card.done = second_play
		self.played_by.discard(selection, self.played_by.played)
		self.game.announce(throne_room_str)
		selected_card.play(True)
		self.played_by.update_resources()
		self.played_by.update_hand()

class Festival(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Festival"
		self.description = "+$2\n +2 actions\n +1 buy"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.actions += 2
		self.played_by.buys += 1
		self.game.announce("-- gaining 2 actions, 1 buy and $2")
		Card.on_finished(self, False)

class Council_Room(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Council Room"
		self.description = "+4 cards\n +1 buy\n Each other player draws a card"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		drawn = self.played_by.draw(4)
		self.played_by.buys += 1
		self.game.announce("-- drawing " + drawn + " and getting +1 buy")
		self.game.announce("-- each other player draws a card")
		for i in self.game.players:
			if (i != self.played_by):
				i.draw(1)
				i.update_hand()
		Card.on_finished(self)

class Laboratory(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Laboratory"
		self.description = "+2 cards\n +1 action"
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.played_by.actions += 1
		self.game.announce("-- drawing " + drawn + " and gaining +1 action")
		Card.on_finished(self)

class Witch(AttackCard):
	def __init__(self, game, played_by):
		AttackCard.__init__(self, game, played_by)
		self.title = "Witch"
		self.description = "+2 cards\n Each other player gains a curse card"
		self.price = 5

	def play(self, skip=False):
		Card.play(self, skip)
		drawn = self.played_by.draw(2)
		self.game.announce("-- drawing " + drawn)
		self.played_by.update_hand()
		self.played_by.update_resources()
		AttackCard.check_reactions(self, self.game.get_opponents(self.played_by))

	def attack(self):
		for i in self.game.get_opponents(self.played_by):
			if not AttackCard.is_blocked(self, i):
				i.gain("Curse")
		Card.on_finished(self, False, False)