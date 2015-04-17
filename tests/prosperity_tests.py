import unittest
import client as c
import base_set as base
import intrigue_set as intrigue
import prosperity_set as prosperity
import card as crd
import game as g
import kingdomGenerator as kg

import sys
import os
# add this file's path to the sys for importing base_tests
sys.path.append(os.path.dirname(__file__))
import base_tests as bt
import intrigue_tests as it


class TestProsperity(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, bt.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, bt.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, bt.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [])
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for i in self.game.players:
			i.game = self.game
			i.setup()
			i.handler.log = []
		self.player1.take_turn()

	# --------------------------------------------------------
	# ---------------------- Prosperity ----------------------
	# --------------------------------------------------------

	def test_Monument(self):
		monument = prosperity.Monument(self.game, self.player1)
		monument.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.vp == 1)

		self.assertTrue(self.player1.total_vp() == 4)

	def test_Counting_House(self):
		counting_house = prosperity.Counting_House(self.game, self.player1)
		copper1 = crd.Copper(self.game, self.player1)
		copper2 = crd.Copper(self.game, self.player1)
		copper3 = crd.Copper(self.game, self.player1)

		num_coppers = self.player1.hand.get_count('Copper')

		self.player1.discard_pile.append(copper1)
		self.player1.discard_pile.append(copper2)
		self.player1.discard_pile.append(copper3)

		counting_house.play()

		self.assertTrue(self.player1.hand.get_count('Copper') == num_coppers + 3)
		self.assertTrue(self.player1.discard_pile)

	def test_Workers_Village(self):
		workers_village = prosperity.Workers_Village(self.game, self.player1)

		workers_village.play()

		self.assertTrue(len(self.player1.hand.card_array()) == 6)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.actions == 2)

	def test_Expand(self):
		expand = prosperity.Expand(self.game, self.player1)

		expand.play()

		self.player1.waiting["cb"](["Copper"])

		self.player1.waiting["cb"](["Silver"])

		self.assertTrue(self.player1.discard_pile[0].title == "Silver")

	def test_Mint(self):
		mint = prosperity.Mint(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)

		mint.play()

		self.assertTrue(self.player1.discard_pile[0].title == "Copper")

		self.player1.hand.add(silver)
		self.player1.hand.add(silver)
		mint.play()

		self.player1.waiting["cb"](["Silver"])
		self.assertTrue(self.player1.discard_pile[1].title == "Silver")

		self.player1.spend_all_money()
		self.player1.buy_card('Mint')
		self.assertTrue(len(self.game.trash_pile) >= 5)

	def test_Mountebank(self):
		mountebank = prosperity.Mountebank(self.game, self.player1)
		curse = crd.Curse(self.game, self.player2)

		self.player2.hand.add(curse)

		mountebank.play()

		self.assertTrue(self.player1.balance == 2)
		self.player2.waiting["cb"](["Yes"])

		self.assertTrue(self.player2.discard_pile[0].title == "Curse")
		self.assertTrue(self.player3.discard_pile[0].title == "Copper")
		self.assertTrue(self.player3.discard_pile[1].title == "Curse")


if __name__ == '__main__':
	unittest.main()