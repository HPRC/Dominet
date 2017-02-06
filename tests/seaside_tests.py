import unittest
import client as c
import unittest.mock
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
	def test_Explorer(self):
		tu.print_test_header("test Explorer")
		explorer = sea.Explorer(self.game, self.player1)
		explorer.play()
		self.assertTrue(self.player1.hand.get_count('Silver') == 1)

		self.player1.actions += 1

		province = supply_cards.Province(self.game, self.player1)
		self.player1.hand.add(province)
		explorer.play()
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.hand.get_count('Gold') == 1)

	def test_Wharf(self):
		tu.print_test_header("test Wharf")
		wharf = sea.Wharf(self.game, self.player1)
		wharf.play()
		self.assertTrue(len(self.player1.hand) == 7)
		self.assertTrue(self.player1.buys == 2)

		wharf.duration()
		self.assertTrue(len(self.player1.hand) == 9)
		self.assertTrue(self.player1.buys == 3)

	@tornado.testing.gen_test
	def test_Sea_Hag(self):
		tu.print_test_header("test Sea Hag")
		sea_hag = sea.Sea_Hag(self.game, self.player1)
		sea_hag.play()
		self.assertTrue(len(self.player2.discard_pile) == 1)
		self.assertTrue(self.player2.topdeck().title == 'Curse')

	@tornado.testing.gen_test
	def test_Pearl_Diver(self):
		tu.print_test_header("test Pearl Diver")
		pearl_diver = sea.Pearl_Diver(self.game, self.player1)
		pearl_diver.play()
		self.assertTrue(len(self.player1.hand) == 6)
		self.assertTrue(self.player1.actions == 1)
		bottom_deck = self.player1.deck[0]
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.topdeck() == bottom_deck)

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

	def test_Fishing_Village(self):
		tu.print_test_header("test Fishing Village")
		fishing_village = sea.Fishing_Village(self.game, self.player1)
		fishing_village.play()
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(self.player1.balance == 1)
		fishing_village.duration()
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(self.player1.balance == 2)

	def test_Merchant_Ship(self):
		tu.print_test_header("test Merchant Ship")
		merchant_ship = sea.Merchant_Ship(self.game, self.player1)
		merchant_ship.play()
		self.assertTrue(self.player1.balance == 2)
		merchant_ship.duration()
		self.assertTrue(self.player1.balance == 4)

	@tornado.testing.gen_test
	def test_Treasure_Map(self):
		tu.print_test_header("test Treasure Map")
		treasure_map = sea.Treasure_Map(self.game, self.player1)
		tu.add_many_to_hand(self.player1, treasure_map, 2)
		treasure_map.play()
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		for i in range (0, 4):
			self.assertTrue(self.player1.deck.pop().title == 'Gold')
		self.assertTrue(self.player1.hand.get_count('Treasure Map') == 0)

	def test_Tactician(self):
		tu.print_test_header("test Tactician")
		tactician = sea.Tactician(self.game, self.player1)
		tactician.play()
		self.assertTrue(len(self.player1.hand) == 0)

		tactician.duration()
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(len(self.player1.hand) == 5)

		tu.set_player_hand(self.player1, [tactician])
		tactician.play()

	@tornado.testing.gen_test
	def test_Treasury(self):
		tu.print_test_header("test Treasury")
		treasury1 = sea.Treasury(self.game, self.player1)
		treasury2 = sea.Treasury(self.game, self.player1)
		self.player1.hand.add(treasury1)
		self.player1.hand.add(treasury2)

		select_future = gen.Future()
		self.player1.select = unittest.mock.Mock(return_value=select_future)
		tu.send_input(self.player1, "play", "Treasury")
		tu.send_input(self.player1, "play", "Treasury")
		self.player1.end_turn()
		self.player1.select.assert_called_once_with(1, 1, [0, 1, 2], unittest.mock.ANY)
		select_future.set_result([2])
		yield gen.sleep(.1)
		self.assertTrue(self.player1.hand.get_count("Treasury") == 2)

	@tornado.testing.gen_test
	def test_Warehouse(self):
		tu.print_test_header("test Warehouse")
		copper = supply_cards.Copper(self.game, self.player1)
		self.player1.hand.add(copper)
		warehouse = sea.Warehouse(self.game, self.player1)
		warehouse.play()

		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(len(self.player1.hand) == 9)

		yield tu.send_input(self.player1, "post_selection", ["Copper", "Copper", "Copper"])
		self.assertTrue(len(self.player1.hand) == 6)

	@tornado.testing.gen_test
	def test_block_sea_hag_3p(self):
		tu.print_test_header("Test block sea hag 3p")
		sea_hag = sea.Sea_Hag(self.game, self.player2)
		self.player2.hand.add(sea_hag)
		self.player1.hand.add(base.Moat(self.game, self.player1))
		self.player3.hand.add(base.Moat(self.game, self.player3))

		self.player1.gain_to_deck = unittest.mock.Mock(return_value=gen.Future())
		player1_select_future = gen.Future()
		self.player1.select = unittest.mock.Mock(return_value=player1_select_future)
		self.player3.gain_to_deck = unittest.mock.Mock(return_value=gen.Future())
		player3_select_future = gen.Future()
		self.player3.select = unittest.mock.Mock(return_value=player3_select_future)
		yield tu.send_input(self.player2, "play", "Sea Hag")
		yield gen.moment
		player1_select_future.set_result(["Reveal"])
		yield gen.sleep(.1)
		player3_select_future.set_result(["Reveal"])
		yield gen.sleep(.1)

		self.assertTrue(self.player1.gain_to_deck.call_count == 0)
		self.assertTrue(self.player3.gain_to_deck.call_count == 0)

	@tornado.testing.gen_test
	def test_Cutpurse(self):
		tu.print_test_header("test Cutpurse")
		cutpurse = sea.Cutpurse(self.game, self.player1)
		self.player1.hand.add(cutpurse)
		discard_future = gen.Future()
		self.player2.discard = unittest.mock.Mock(return_value=discard_future)
		self.player3.discard = unittest.mock.Mock(return_value=gen.Future())
		balance = self.player1.balance
		tu.send_input(self.player1, "play", "Cutpurse")
		
		self.assertTrue(self.player1.balance == balance + 2)
		self.player2.discard.assert_called_with(['Copper'], self.player2.discard_pile)
		discard_future.set_result([])
		yield gen.moment
		self.player3.discard.assert_called_with(['Copper'], self.player3.discard_pile)

if __name__ == '__main__':
		unittest.main()