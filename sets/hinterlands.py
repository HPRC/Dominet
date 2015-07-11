import sets.card as crd
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
