import unittest
import net
import client as c
import game as g
import card as crd
import cardpile as cp

class DummyHandler():
	def write_json(self, **kwargs):
		if ("command" in kwargs and kwargs["command"] == "announce"):
			print(kwargs["msg"])
		pass
class SilentHandler():
	def write_json(self, **kwargs):
		pass

class TestGame(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, DummyHandler())
		self.player2 = c.DmClient("player2", 1, SilentHandler())
		self.game = g.DmGame([self.player1, self.player2])
		for i in self.game.players:
			i.game = self.game
			i.setup()

	def test_inital_decks(self):
		self.assertTrue(len(self.player1.deck) == 5)

	def test_remove_from_supply(self):
		self.assertTrue(self.game.supply.get_count("Estate") == 8)
		self.assertTrue(self.game.base_supply.get_count("Estate") == 8)
		self.game.remove_from_supply("Estate")
		self.assertTrue(self.game.supply.get_count("Estate") == 7)
		self.assertTrue(self.game.base_supply.get_count("Estate") == 7)

	def test_total_vp(self):
		initial_vp = self.player1.total_vp()
		self.player1.gain("Province")
		self.assertTrue(self.player1.total_vp() == initial_vp + 6)

	def test_gain(self):
		initialCurses = self.game.supply.get_count("Curse")
		self.player2.gain("Curse")
		self.assertTrue(self.player2.discard_pile[-1].title == "Curse")
		self.assertTrue(self.game.supply.get_count("Curse") == initialCurses-1)

	def test_detect_end(self):
		for i in range(0,8):
			self.player1.gain("Province")
		self.assertTrue(self.game.detect_end())

	def test_end_tie(self):
		self.game.turn = 1
		for i in range(0,4):
			self.player1.gain("Province")
			self.player2.gain("Province")
		self.assertTrue(self.game.detect_end())

	def test_spend_all_money(self):
		self.player1.balance = 0
		self.player1.hand = cp.HandPile(self.player1)
		copper = crd.Copper(self.game, self.player1)
		for i in range(0,5):
			self.player1.hand.add(copper)
		self.player1.spend_all_money()
		self.assertTrue(self.player1.balance == 5)
		self.assertTrue(len(self.player1.hand) == 0)
		self.assertTrue(len(self.player1.played) == 5)

	def test_discard(self):
		self.player1.hand = cp.HandPile(self.player1)
		self.player1.hand.add(crd.Copper(self.game, self.player1))
		self.player1.discard(["Copper"], self.player1.discard_pile)
		self.assertTrue(len(self.player1.hand) == 0)

if __name__ == '__main__':
	unittest.main()