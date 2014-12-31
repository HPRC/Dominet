import unittest
import net
import client as c

class DummyHandler():
	def write_json(self, **kwargs):
		pass

class TestGame(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, DummyHandler())
		self.player2 = c.DmClient("player2", 1, DummyHandler())
		self.game = net.DmGame([self.player1, self.player2])
		for i in self.game.players:
			i.game = self.game
			i.setup()

	def test_inital_decks(self):
		self.assertTrue(len(self.player1.deck) == 5)

	def test_remove_from_supply(self):
		self.assertTrue(self.game.supply["Estate"][1] == 8)
		self.assertTrue(self.game.base_supply["Estate"][1] == 8)
		self.game.remove_from_supply("Estate")
		self.assertTrue(self.game.supply["Estate"][1] == 7)
		self.assertTrue(self.game.base_supply["Estate"][1] == 7)

	def test_total_vp(self):
		self.assertTrue(self.player1.total_vp() == 3)

	def test_detect_end(self):
		for i in range(0,8):
			self.player1.gain("Province")
		self.assertTrue(self.game.detect_end())

	# def test_detect_end_piles(self):
	# 	for title, data in self.game.supply.items():
	# 		self.


if __name__ == '__main__':
	unittest.main()