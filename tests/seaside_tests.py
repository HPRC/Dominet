import unittest
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.prosperity as prosperity
import sets.supply as supply_cards
import sets.seaside as sea
import game as g
import kingdomGenerator as kg

import tornado.testing
from tornado import gen
import tests.test_utils as tu


class TestSeaside(tornado.testing.AsyncTestCase):
	def setUp(self):
		super().setUp()
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [], test=True)
		self.game.players = [self.player1, self.player2, self.player3]
		for i in self.game.players:
			i.game = self.game
		self.game.start_game()
		self.player1.take_turn()

	def test_Lighthouse(self):
		tu.print_test_header("test Lighthouse")
		lighthouse = sea.Lighthouse(self.game, self.player1)
		lighthouse.play()
		militia = base.Militia(self.game, self.player2)
		self.assertTrue(militia.is_blocked(self.player1))
		self.assertTrue(militia.is_blocked(self.player1))
		lighthouse.duration()
		self.assertFalse(militia.is_blocked(self.player1))

	@tornado.testing.gen_test
	def test_Salvager(self):
		tu.print_test_header("test Salvager")
		salvager = sea.Salvager(self.game, self.player1)
		province = supply_cards.Province(self.game, self.player1)
		self.player1.hand.add(province)
		salvager.play()
		yield tu.send_input(self.player1, "post_selection", ["Province"])
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.balance == 8)

if __name__ == '__main__':
		unittest.main()