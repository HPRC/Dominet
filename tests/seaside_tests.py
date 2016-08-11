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

	def test_Merchant_Ship(self):
		tu.print_test_header("test Merchant Ship")
		merchant_ship = sea.Merchant_Ship(self.game, self.player1)
		merchant_ship.play()
		self.assertTrue(self.player1.balance == 2)
		merchant_ship.duration()
		self.assertTrue(self.player1.balance == 4)

	@tornado.testing.gen_test
	def test_Treasure_map(self):
		tu.print_test_header("test Treasure Map")
		treasure_map = sea.Treasure_Map(self.game, self.player1)
		tu.add_many_to_hand(self.player1, treasure_map, 2)
		treasure_map.play()
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		for i in range (0, 4):
			self.assertTrue(self.player1.deck.pop().title == 'Gold')
		self.assertTrue(self.player1.hand.get_count('Treasure Map') == 0)


if __name__ == '__main__':
		unittest.main()