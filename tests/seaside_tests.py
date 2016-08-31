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

	def test_Caravan(self):
		tu.print_test_header("test Caravan")
		caravan = sea.Caravan(self.game, self.player1)
		hand_count = len(self.player1.hand)
		caravan.play()
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(len(self.player1.hand) == hand_count + 1)
		caravan.duration()
		self.assertTrue(len(self.player1.hand) == hand_count + 2)

	def test_Bazaar(self):
		tu.print_test_header("test Bazaar")
		bazaar = sea.Bazaar(self.game, self.player1)
		bazaar.play()
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(len(self.player1.hand) == 6)
		self.assertTrue(self.player1.balance == 1)


	@tornado.testing.gen_test
	def test_Treasury(self):
		tu.print_test_header("test Treasury")
		treasury = sea.Treasury(self.game, self.player1)

		tu.add_many_to_hand(self.player1, treasury, 2)

		tu.send_input(self.player1, "play", "Treasury")
		tu.send_input(self.player1, "play", "Treasury")
		self.player1.buy_card('Copper')
		self.player1.end_turn()

		yield tu.send_input(self.player1, "post_selection", [2])
		self.assertTrue(self.player1.hand.get_count("Treasury") == 2)


if __name__ == '__main__':
		unittest.main()