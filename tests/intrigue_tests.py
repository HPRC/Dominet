import unittest
import client as c
import base_set as base
import intrigue_set as intrigue
import card as crd
import game as g
import kingdomGenerator as kg

import sys
import os
#add this file's path to the sys for importing base_tests
sys.path.append(os.path.dirname(__file__))
import base_tests as bt

class TestIntrigue(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, bt.Player1Handler())
		self.player2 = c.DmClient("player2", 1, bt.Player2Handler())
		self.game = g.DmGame([self.player1, self.player2], [])
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for i in self.game.players:
			i.game = self.game
			i.setup()
		self.player1.take_turn()
		bt.Player1Handler.log = []
		bt.Player2Handler.log = []


	# --------------------------------------------------------
	# ----------------------- Intrigue -----------------------
	# --------------------------------------------------------

	def test_Baron(self):
		baron = intrigue.Baron(self.game, self.player1)
		self.player1.hand.data = {}
		self.player1.hand.add(baron, 3)
		estate = crd.Estate(self.game, self.player1)
		# sadly add an estate to hand since no guarantees -- actually overwrites hand
		self.player1.hand.add(estate)
		self.player1.actions = 3


		# decline Estate discard, gain Estate to discard pile.
		baron.play()
		self.player1.waiting["cb"](["No"])
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(len(self.player1.discard_pile) == 1)

		# accept Estate discard, do not gain Estate to discard pile, gain $4
		baron.play()
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.buys == 3)
		self.assertTrue(self.player1.balance == 4)
		self.assertFalse("Estate" in self.player1.hand)

		# Not given option because no Estates in hand.
		baron.play()
		self.assertTrue(self.player1.buys == 4)

	def test_Shanty_Town(self):
		shanty_town = intrigue.Shanty_Town(self.game, self.player1)
		self.player1.hand.add(shanty_town, 2)

		# First Play: has an action, should not draw cards.
		cards_in_hand = len(self.player1.hand)
		shanty_town.play()
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(len(self.player1.hand) == cards_in_hand - 1)

		# Second Play: has no other action cards in hand, should draw cards.
		shanty_town.play()
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(len(self.player1.hand) == cards_in_hand)

	def test_Conspirator(self):
		conspirator = intrigue.Conspirator(self.game, self.player1)
		self.player1.hand.add(conspirator, 2)

		village = base.Village(self.game, self.player1)
		self.player1.hand.add(village)

		village.play()
		conspirator.play()
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.balance == 2)

		cards_in_hand = len(self.player1.hand)
		conspirator.play()
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(len(self.player1.hand) == cards_in_hand)

	def test_Courtyard(self):
		courtyard = intrigue.Courtyard(self.game, self.player1)
		self.player1.hand.add(courtyard)

		cards_in_hand = len(self.player1.hand)

		courtyard.play()
		self.player1.waiting["cb"](["Copper"])

		self.assertTrue(len(self.player1.hand) == cards_in_hand + 1)
		topdeck = self.player1.topdeck()
		self.assertTrue(topdeck.title == "Copper")

	def test_Nobles(self):
		nobles = intrigue.Nobles(self.game, self.player1)
		self.player1.hand.add(nobles, 2)

		nobles.play()
		self.player1.waiting["cb"](["+2 Actions"])
		self.assertTrue(self.player1.actions == 2)

		cards_in_hand = len(self.player1.hand)

		nobles.play()
		self.player1.waiting["cb"](["+3 Cards"])
		self.assertTrue(len(self.player1.hand) == cards_in_hand + 2)

	def test_Swindler(self):
		swindler = intrigue.Swindler(self.game, self.player1)
		self.player2.deck.append(crd.Copper(self, self.player2))
		self.player1.hand.add(swindler, 1)

		swindler.play()

		self.player1.waiting["cb"]("Curse")

	def test_Duke(self):
		duke = intrigue.Duke(self.game, self.player1)
		self.player1.hand.add(duke, 1)

		duchy = crd.Duchy(self.game, self.player1)
		self.player1.hand.add(duchy, 1)
		self.player1.deck.append(duchy)
		self.player1.discard_pile.append(duchy)

		self.assertTrue(duke.get_vp(), 3)

	def test_Wishing_Well(self):
		wishing_well = intrigue.Wishing_Well(self.game, self.player1)
		self.player1.hand.add(wishing_well, 2)
		province = crd.Province(self.game, self.player1)
		self.player1.deck.append(province)
		self.player1.deck.append(province)

		wishing_well.play()
		self.player1.waiting["cb"]("Province")
		self.assertTrue(self.player1.hand.get_count('Province'), 1)

		wishing_well.play()
		self.player1.waiting["cb"]("Copper")
		self.assertTrue(self.player1.hand.get_count('Province'), 1)

	def test_Upgrade(self):
		upgrade = intrigue.Upgrade(self.game, self.player1)
		self.player1.hand.add(upgrade, 2)

		upgrade.play()
		self.player1.waiting["cb"](["Copper"])

		upgrade.play()
		self.player1.waiting["cb"](["Estate"])

	def test_Torturer(self):
		torturer = intrigue.Torturer(self.game, self.player1)
		self.player1.hand.add(torturer, 2)
		self.player1.actions = 2

		torturer.play()
		# choosing to discard 2
		self.player2.waiting["cb"](["Discard 2 cards"])
		self.player2.waiting["cb"](['Copper', 'Copper'])

		torturer.play()
		self.player2.waiting["cb"](["Gain a Curse"])
		self.assertTrue(self.player2.hand.get_count('Curse'), 1)

		self.player1.actions = 1
		copper = crd.Copper(self.game, self.player1)
		self.player2.hand.data = {
			"Copper": [copper, 3]
		}
		torturer.play()
		self.player2.waiting["cb"](["Discard 2 cards"])

	def test_Trading_Post(self):
		trading_post = intrigue.Trading_Post(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.data = {
			"Copper": [copper, 1],
			"Trading Post": [trading_post, 1]
		}
		self.player1.actions = 3

		trading_post.play()
		self.assertTrue(len(self.player1.hand.data) == 0, True)

		self.player1.hand.data = {
			"Copper": [copper, 2],
			"Trading Post": [trading_post, 1]
		}
		trading_post.play()
		self.assertTrue(self.player1.hand.get_count("Silver"), 1)

		self.player1.hand.add(trading_post, 3)
		trading_post.play()
		self.player1.waiting["cb"](["Trading Post", "Trading Post"])
		self.assertTrue(self.player1.hand.get_count("Silver"), 2)

	def test_Ironworks(self):
		ironworks = intrigue.Ironworks(self.game, self.player1)
		self.player1.hand.add(ironworks, 4)
		self.player1.actions = 2

		ironworks.play()
		self.player1.waiting["cb"]("Steward")
		self.assertTrue(self.player1.actions, 2)

		ironworks.play()
		self.player1.waiting["cb"]("Silver")
		self.assertTrue(self.player1.balance, 1)

		ironworks.play()
		cards_in_hand = len(self.player1.hand.card_array())
		self.player1.waiting["cb"]("Great Hall")
		self.assertTrue(self.player1.actions, 1)
		self.assertTrue(self.player1.hand, cards_in_hand + 1)


if __name__ == '__main__':
	unittest.main()