import sets.card as crd

# --------------------------------------------------------
# ------------------------ 2 Cost ------------------------
# --------------------------------------------------------

class Crossroads(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Crossroads"
		self.description = "Reveal hand.\n +1 Card per Victory card.\n The first time you play this per turn, +3 Actions."
		self.price = 2
		self.type = "Action"

	def play(self, skip=False):
		cards_played = list(map(lambda x : x.title, self.played_by.played))
		crd.Card.play(self, skip)
		#Announce announces everything to all players in log, reveal_string adds css to cards in log 
		self.game.announce("-- reveals " + self.played_by.hand.reveal_string())
		num_victory_cards = len(self.played_by.hand.get_cards_by_type("Victory"))
		drawn = self.played_by.draw(num_victory_cards)
		#needs to be part of crossroads log
		self.game.announce("-- draws " + drawn)
		if "Crossroads" not in cards_played:
			self.played_by.actions += 3
		crd.Card.on_finished(self, True)


# --------------------------------------------------------
# ------------------------ 4 Cost ------------------------
# --------------------------------------------------------


class Nomad_Camp(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Nomad Camp"
		self.description = "+1 Buy, +$2\n When you gain this, put it on top of your deck"
		self.price = 4
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 2
		self.played_by.buys += 1
		crd.Card.on_finished(self, False)

	def on_gain(self):
		self.played_by.discard_pile.remove(self)
		self.played_by.deck.append(self)
		self.game.announce("-- adding " + self.log_string() + " to the top of their deck")


class Trader(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Trader"
		self.description = "Trash a card from your hand, Gain X Silvers where X is the cost of the trash card. Whenever you gain a card, you may\
			reveal Trader to gain a Silver instead"
		self.price = 4
		self.type = "Action|Reaction"
		self.trigger = "Gain"
		self.reacted_to_callback = None

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),  
			"Select card to trash")
		self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		trashed = self.played_by.hand.get_card(selection[0])
		self.played_by.discard(selection, self.game.trash_pile)
		self.game.update_trash_pile()
		self.game.announce("-- trashing " + self.game.log_string_from_title(selection[0]))
		for i in range(0, trashed.get_price()):
			self.played_by.gain("Silver", suppress_announcement=True)
		self.game.announce("-- gaining " + str(trashed.get_price()) + " " + self.game.log_string_from_title("Silver", trashed.get_price() > 1))
		crd.Card.on_finished(self, True)

	def react(self, reacted_to_callback, to_gain):
		self.reacted_to_callback = reacted_to_callback
		turn_owner = self.game.get_turn_owner()
		if self.played_by != turn_owner:
			turn_owner.wait("to react", self.played_by)

		self.played_by.select(1, 1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to return " + to_gain.title + " to the supply and gain a Silver instead?")
			
		self.played_by.set_cb(self.post_reveal)

	def post_reveal(self, selection):
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			to_gain = self.played_by.discard_pile.pop()
			self.game.supply.add(to_gain)
			self.game.update_supply_pile(to_gain.title)
			self.game.announce("-- returning " + to_gain.log_string() + " to supply")
			self.played_by.gain("Silver")
		temp = self.reacted_to_callback
		self.reacted_to_callback = None
		temp()

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])

# --------------------------------------------------------
# ------------------------ 5 Cost ------------------------
# --------------------------------------------------------

class Mandarin(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Mandarin"
		self.description = "+$3, Put a card from your hand on top of your deck. \
		When you gain this, put all treasures in play on top of your deck in any order."
		self.price = 5
		self.type = "Action"

	def play(self, skip=False):
		crd.Card.play(self, skip)
		self.played_by.balance += 3
		self.game.announce("-- gaining +$3")
		top_select = self.played_by.hand.auto_select(1, False)
		if top_select:
			self.post_select(top_select)
		else:
			self.played_by.select(1, 1, crd.card_list_to_titles(self.played_by.hand.card_array()),  
				"Select card to put back on top of your deck")
			self.played_by.set_cb(self.post_select)

	def post_select(self, selection):
		self.played_by.discard(selection, self.played_by.deck)
		self.played_by.announce_opponents("-- placing a card back on top of their deck")
		card_string = self.game.log_string_from_title(selection[0])
		self.played_by.announce_self("-- You place " + card_string + " back on top of your deck")
		crd.Card.on_finished(self, True)

	def on_gain(self):
		played_treasures = [x for x in self.played_by.played if "Treasure" in x.type]
		#remove treasures from played pile
		self.played_by.played = [x for x in self.played_by.played if "Treasure" not in x.type]
		if len(played_treasures) == 1 or len(set(map(lambda x: x.title, played_treasures))) == 1:
			self.game.announce("-- placing treasures back on top of their deck")
			self.played_by.deck += played_treasures
		else:
			crd.reorder_top(self.played_by, played_treasures, self.done_gaining)

	def done_gaining(self):
		self.game.announce("-- placing treasures back on top of their deck")
		if self.game.get_turn_owner() == self.played_by:
			self.played_by.update_mode()

