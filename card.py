class Card():
	def __init__(self, game, played_by):
		self.game = game
		self.played_by = played_by
		self.title = None
		self.type = None
		self.description = None
		self.price = None
		self.done = lambda: None

	def play(self, skip=False):
		if not skip:
			self.played_by.discard([self.title], self.played_by.played)
			self.game.announce(self.played_by.name_string() + " played " + self.log_string())
			if "Action" in self.type:
				self.played_by.actions -= 1

	def get_price(self):
		return self.price + self.game.price_modifier

	# called at the end of a card's resolution
	def on_finished(self, modified_hand=True, modified_resources=True):
		if modified_resources:
			self.played_by.update_resources()
		if modified_hand:
			self.played_by.update_hand()
		self.played_by.update_mode()
		self.played_by.waiting["cb"] = None
		self.done()

	def to_json(self):
		return {
			"title": self.title,
			"type": self.type,
			"description": self.description,
			"price": self.price
		}

	#called at the end of turn if this card was played
	def cleanup(self):
		pass

	def log_string(self, plural=False):
		return "".join(["<span class='label label-default'>", self.title, "s</span>" if plural else "</span>"])


class Money(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Treasure"
		self.value = None

	def play(self, skip=False):
		Card.play(self, skip)
		self.played_by.balance += self.value
		self.played_by.update_resources(True)

	# override
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
		#dictionary of reacting player client instance : list of reaction card callbacks to call
		self.reactions = {}

	# called after reaction card finishes
	# reacting_player = owner of reactio card that just finished
	def reacted(self, reacting_player, drew_cards=False):
		#if we drew any new cards during a card's reaction reprompt all reactions since player may
		#want to reveal cards again
		if drew_cards:
			self.reactions[reacting_player] = []
			for x in reacting_player.hand.get_cards_by_type("Reaction"):
				self.reactions[reacting_player].append(x.react)
		if len(self.reactions[reacting_player]) == 0:
			del self.reactions[reacting_player]
			if not self.reactions:
				self.attack()
			else:
				#we still have reactions but no more for this player, move onto next
				for i in range(1, len(self.game.players)+1):
					next_index = (i + self.game.players.index(reacting_player)) % len(self.game.players)
					if self.game.players[next_index] in self.reactions:
						reacting(lambda drew_cards=False: self.reacted(self.game.players[next_index], drew_cards))
						break
		else:
			reacting = self.reactions[reacting_player].pop()
			reacting(lambda drew_cards=False: self.reacted(reacting_player, drew_cards))

	def check_reactions(self, targets):
		for i in targets:
			reaction_cards = i.hand.get_cards_by_type("Reaction")
			for card in reaction_cards:
				if card.trigger == "Attack":
					if i in self.reactions:
						self.reactions[i].append(card.react)
					else:
						self.reactions[i] = [card.react]
		if not self.reactions:
			self.attack()
		else:
			attacker_index = self.game.players.index(self.played_by)
			for i in range(1, len(self.game.players)+1):
				next_index = (i + attacker_index) % len(self.game.players)
				next_player = self.game.players[next_index]
				if next_player in self.reactions:
					self.reacted(next_player)
					break

	def is_blocked(self, target):
		# shouldnt need to block against own attacks (i.e. spy)
		if target.protection == 0 or target == self.played_by:
			return False
		else:
			target.protection -= 1
			self.game.announce(target.name_string() + " is unaffected by the attack")
			return True

	# used in cards where we have to wait on each player to make a selection or something
	# if not blocked then continue the attack and a post_select or choice will trigger the get_next
	def fire(self, player):
		if not self.is_blocked(player):
			return True
		else:
			self.get_next(player)
	
	# should call get next of player of the attack first (or player if inclusive)
	# chooses the next person from the last until we reach the player to stop
	def get_next(self, victim):
		next_player_index = (self.game.players.index(victim) + 1) % len(self.game.players)
		if self.game.players[next_player_index] != self.played_by:
			self.fire(self.game.players[next_player_index])
		else:
			Card.on_finished(self)

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


class Platinum(Money):
	def __init__(self, game, played_by):
		Money.__init__(self, game, played_by)
		self.title = "Platinum"
		self.value = 5
		self.price = 9
		self.description = "+$5"


class Curse(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.title = "Curse"
		self.description = "-1 VP"
		self.price = 0
		self.vp = -1
		self.type = "Curse"

	def get_vp(self):
		return self.vp
		
	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-curse'>", self.title, "s</span>" if plural else "</span>"])

class VictoryCard(Card):
	def __init__(self, game, played_by):
		Card.__init__(self, game, played_by)
		self.type = "Victory"

	def get_vp(self):
		return self.vp

	def play(self):
		return

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", self.title, "s</span>" if plural else "</span>"])


class Estate(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Estate"
		self.description = "+1 VP"
		self.price = 2
		self.vp = 1


class Duchy(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Duchy"
		self.description = "+3 VP"
		self.price = 5
		self.vp = 3

	def log_string(self, plural=False):
		return "".join(["<span class='label label-success'>", "Duchies</span>" if plural else self.title, "</span>"])


class Province(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Province"
		self.description = "+6 VP"
		self.price = 8
		self.vp = 6


class Colony(VictoryCard):
	def __init__(self, game, played_by):
		VictoryCard.__init__(self, game, played_by)
		self.title = "Colony"
		self.description = "+10 VP"
		self.price = 11
		self.vp = 10


# Utility
# returns list of card titles from list of card jsons or card objects
def card_list_to_titles(lst):
	if len(lst) == 0:
		return []
	return list(map(lambda x: x['title'], lst)) if isinstance(lst[0], dict) else list(map(lambda x: x.title, lst))


def card_list_log_strings(lst):
	return list(map(lambda x: x.log_string(), lst))



