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


class Trader(crd.Card):
	def __init__(self, game, played_by):
		crd.Card.__init__(self, game, played_by)
		self.title = "Trader"
		self.description = "Trash a card from your hand, Gain X Silvers where X is the cost of the trash card. Whenever you gain a card, you may\
			reveal Trader to trash it and gain a Silver instead"
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
		for i in range(0, trashed.get_price()):
			self.played_by.gain("Silver", suppress_announcement=True)
		self.game.announce("-- gaining " + str(trashed.get_price()) + " " + self.game.log_string_from_title("Silver", trashed.price > 1))
		crd.Card.on_finished(self, False)

	def react(self, reacted_to_callback, to_gain):
		self.reacted_to_callback = reacted_to_callback
		turn_owner = self.game.get_turn_owner()
		if self.played_by != turn_owner:
			turn_owner.wait("to react", self.played_by)

		self.played_by.select(1, 1, ["Reveal", "Hide"],  
			"Reveal " + self.title + " to trash " + to_gain.title + " and gain a Silver instead?")
			
		self.played_by.set_cb(self.post_reveal)

	def post_reveal(self, selection):
		if selection[0] == "Reveal":
			self.game.announce(self.played_by.name_string() + " reveals " + self.log_string())
			to_gain = self.played_by.discard_pile.pop()
			self.game.trash_pile.append(to_gain)
			self.game.update_trash_pile()
			self.game.announce("-- trashing " + to_gain.log_string())
			self.played_by.gain("Silver")
		temp = self.reacted_to_callback
		self.reacted_to_callback = None
		temp()

	def log_string(self, plural=False):
		return "".join(["<span class='label label-info'>", self.title, "s</span>" if plural else "</span>"])
