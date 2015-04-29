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
# add this file's path to the sys for importing test_utils
sys.path.append(os.path.dirname(__file__))
import test_utils as tu


class TestProsperity(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [])
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for i in self.game.players:
			i.game = self.game
			i.setup()
			i.handler.log = []
		self.game.players = [self.player1, self.player2, self.player3]
		self.player1.take_turn()

	# --------------------------------------------------------
	# ---------------------- Prosperity ----------------------
	# --------------------------------------------------------

	def test_Monument(self):
		tu.print_test_header("test Monument")
		monument = prosperity.Monument(self.game, self.player1)
		monument.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.vp == 1)

		self.assertTrue(self.player1.total_vp() == 4)

	def test_Counting_House(self):
		tu.print_test_header("test Counting House")
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
		tu.print_test_header("test Worker's Village")
		workers_village = prosperity.Workers_Village(self.game, self.player1)

		workers_village.play()

		self.assertTrue(len(self.player1.hand.card_array()) == 6)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.actions == 2)

	def test_Expand(self):
		tu.print_test_header("testing expand")
		expand = prosperity.Expand(self.game, self.player1)

		expand.play()

		self.player1.waiting["cb"](["Copper"])

		self.player1.waiting["cb"](["Silver"])

		self.assertTrue(self.player1.discard_pile[0].title == "Silver")

	def test_Watchtower_play(self):
		tu.print_test_header("testing Watchtower play action")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		watchtower2 = prosperity.Watchtower(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		tu.set_player_hand(self.player1, [watchtower, estate, watchtower2])
		self.player1.actions = 2
		watchtower.play()
		#3 cards in hand
		self.assertTrue(len(self.player1.hand) == 6)
		#7 cards in hand
		tu.set_player_hand(self.player1, [estate, estate, watchtower2, estate, estate, estate, estate])
		watchtower2.play()
		self.assertTrue(len(self.player1.hand) == 6)

	def test_Watchtower_react(self):
		tu.print_test_header("testing Watchtower reaction")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		tu.set_player_hand(self.player1, [watchtower])
		self.player1.buy_card("Silver")
		#0 buys should end turn normally but we have a reaction so should still be player1's turn
		self.assertTrue(self.game.get_turn_owner().name == self.player1.name)

		self.player1.exec_commands({"command":"post_selection", "selection":["Reveal"]})
		self.player1.exec_commands({"command":"post_selection", "selection":["Put on top of deck"]})
		self.assertTrue(len(self.player1.discard_pile) == 0)
		self.assertTrue(self.player1.deck[-1].title == "Silver")

		self.player1.end_turn()
		witch = base.Witch(self.game, self.player2)
		self.player2.hand.add(witch)
		watchtower2 = prosperity.Watchtower(self.game, self.player1)
		self.player1.hand.add(watchtower2)

		witch.play()
		self.player1.exec_commands({"command":"post_selection", "selection":["Reveal"]})
		self.player1.exec_commands({"command":"post_selection", "selection":["Trash"]})
		self.assertTrue(self.game.trash_pile[-1].title == "Curse")

	def test_Kings_Court(self):
		tu.print_test_header("testing King's Court")
		conspirator = intrigue.Conspirator(self.game, self.player1)
		kings_court = prosperity.Kings_Court(self.game, self.player1)
		tu.set_player_hand(self.player1, [conspirator, kings_court])
		kings_court.play()
		self.player1.waiting["cb"](["Conspirator"])
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(self.player1.balance == 6)
		#conspirator should be triggered twice, we drew 2 cards
		self.assertTrue(len(self.player1.hand) == 2)


if __name__ == '__main__':
	unittest.main()