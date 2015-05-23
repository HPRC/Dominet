import unittest
import net
import client as c
import game as g
import card as crd
import base_set as base
import cardpile as cp

import sys
import os
sys.path.append(os.path.dirname(__file__))
import test_utils as tu


class DummyHandler():
	def write_json(self, **kwargs):
		if "command" in kwargs and kwargs["command"] == "announce":
			print(kwargs["msg"])
		pass


class SilentHandler():
	def write_json(self, **kwargs):
		pass


class TestGame(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, DummyHandler())
		self.player2 = c.DmClient("player2", 1, SilentHandler())
		self.player3 = c.DmClient("player3", 2, SilentHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [])
		self.game.players = [self.player1, self.player2, self.player3]
		for i in self.game.players:
			i.game = self.game
			i.setup()

	def test_initial_decks(self):
		tu.print_test_header("test initial decks")
		self.assertTrue(len(self.player1.deck) == 5)

	def test_remove_from_supply(self):
		tu.print_test_header("test remove from supply")
		self.assertTrue(self.game.supply.get_count("Estate") == 12)
		self.assertTrue(self.game.base_supply.get_count("Estate") == 12)
		self.game.remove_from_supply("Estate")
		self.assertTrue(self.game.supply.get_count("Estate") == 11)
		self.assertTrue(self.game.base_supply.get_count("Estate") == 11)

	def test_total_vp(self):
		tu.print_test_header("test total vp")
		initial_vp = self.player1.total_vp()
		self.player1.gain("Province")
		self.assertTrue(self.player1.total_vp() == initial_vp + 6)

	def test_gain(self):
		tu.print_test_header("test gain")
		initialCurses = self.game.supply.get_count("Curse")
		self.player2.gain("Curse")
		self.assertTrue(self.player2.discard_pile[-1].title == "Curse")
		self.assertTrue(self.game.supply.get_count("Curse") == initialCurses-1)

	def test_detect_end(self):
		tu.print_test_header("test detect end")
		for i in range(0, 12):
			self.player1.gain("Province")
		self.assertTrue(self.game.detect_end())

	def test_end_tie(self):
		tu.print_test_header("test end tie")
		self.game.turn = 1
		for i in range(0, 6):
			self.player1.gain("Province")
			self.player2.gain("Province")
		self.assertTrue(self.game.detect_end())

	def test_spend_all_money(self):
		tu.print_test_header("test spend all money")
		self.player1.balance = 0
		self.player1.deck = []
		self.player1.hand = cp.HandPile(self.player1)
		copper = crd.Copper(self.game, self.player1)
		for i in range(0, 5):
			self.player1.hand.add(copper)
		self.player1.spend_all_money()
		self.assertTrue(self.player1.balance == 5)
		self.assertTrue(len(self.player1.hand) == 0)
		self.assertTrue(len(self.player1.played) == 5)
		self.assertTrue(len([x for x in self.player1.all_cards() if x.title == "Copper"]) == 5)

	def test_discard(self):
		tu.print_test_header("test discard")
		self.player1.hand = cp.HandPile(self.player1)
		self.player1.hand.add(crd.Copper(self.game, self.player1))
		self.player1.discard(["Copper"], self.player1.discard_pile)
		self.assertTrue(len(self.player1.hand) == 0)

	def test_spam_cb(self):
		tu.print_test_header("test spam cb")
		self.player1.hand.add(base.Remodel(self.game, self.player1))
		self.player1.hand.add(crd.Silver(self.game, self.player1))
		self.player1.hand.add(crd.Silver(self.game, self.player1))

		self.player1.exec_commands({"command":"play", "card": "Remodel"})
		self.player1.exec_commands({"command":"post_selection", "selection": ["Silver"]})
		self.player1.exec_commands({"command":"selectSupply", "card": ["Duchy"]})
		self.assertTrue(self.player1.waiting["cb"] == None)
		self.player1.exec_commands({"command":"selectSupply", "card": ["Duchy"]})
		self.assertTrue(len(self.player1.discard_pile) == 1)

	#tests gaining a card not available anymore doesnt lead to deadlock
	def test_has_selectable(self):
		tu.print_test_header("test has selectable")
		#2 Remodels in hand
		tu.add_many_to_hand(self.player1, base.Remodel(self.game, self.player1), 2)
		#nothing in supply except remodel and gold both at 0 left
		self.game.supply.data = {"Remodel": [base.Remodel(self.game, None), 0], "Gold": [crd.Gold(self.game, None), 0]}
		#try to remodel another remodel
		self.player1.exec_commands({"command":"play", "card": "Remodel"})
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.player1.exec_commands({"command":"post_selection", "selection": ["Remodel"]})

		self.assertTrue(self.player1.last_mode["mode"] != "selectSupply")

	def test_get_opponent_order(self):
		player1opponents = self.player1.get_opponents()
		self.assertTrue(player1opponents[0] == self.player2)
		self.assertTrue(player1opponents[1] == self.player3)
		player2opponents = self.player2.get_opponents()
		self.assertTrue(player2opponents[0] == self.player3)
		self.assertTrue(player2opponents[1] == self.player1)
		player3opponents = self.player3.get_opponents()
		self.assertTrue(player3opponents[0] == self.player1)
		self.assertTrue(player3opponents[1] == self.player2)


if __name__ == '__main__':
	unittest.main()