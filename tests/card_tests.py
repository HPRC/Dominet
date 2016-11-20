import unittest
import unittest.mock
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.prosperity as prosperity
import sets.seaside as sea
import sets.supply as supply_cards
import sets.card as crd
import game as g
import kingdomGenerator as kg

from tornado import gen
import tornado.testing
import tests.test_utils as tu

class TestCard(tornado.testing.AsyncTestCase):
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

	# --------------------------------------------------------
	# ------------------------- Base -------------------------
	# --------------------------------------------------------
 
	@tornado.testing.gen_test
	def test_Duration(self):
		tu.print_test_header("Test Duration on_finished adds duration to durations")
		duration_card = crd.Duration(self.game, self.player1)
		duration_card.title = "Dummy Duration"
		duration_card.duration = unittest.mock.Mock()
		self.player1.hand.add(duration_card)
		duration_card.play()
		self.assertTrue(duration_card in self.player1.durations)
		self.assertTrue(duration_card not in self.player1.played_cards)
		duration_card.on_finished()
		self.assertTrue(duration_card.duration in self.player1.duration_cbs)

	@tornado.testing.gen_test
	def test_Resolve_Duration(self):
		tu.print_test_header("Test take turn resolves durations")
		duration_card = crd.Duration(self.game, self.player1)
		duration_card.duration = unittest.mock.Mock()
		self.player1.duration_cbs.append(duration_card.duration)
		self.player1.durations.append(duration_card)
		yield self.player1.take_turn()
		self.assertTrue(duration_card.duration not in self.player1.duration_cbs)
		self.assertTrue(duration_card.duration.call_count == 1)
		self.assertTrue(duration_card in self.player1.played_cards)
		self.assertTrue(duration_card not in self.player1.durations)

	@tornado.testing.gen_test
	def test_kc_kc_duration(self):
		tu.print_test_header("Test king's court king's court duration")
		kc = prosperity.Kings_Court(self.game, self.player1)
		caravan = sea.Caravan(self.game, self.player1)
		tu.add_many_to_hand(self.player1, kc, 2)
		tu.add_many_to_hand(self.player1, caravan, 3)

		player1_kc_1_select_future = gen.Future()
		player1_kc_2_select_future = gen.Future()
		player1_kc_3_select_future = gen.Future()
		player1_kc_4_select_future = gen.Future()
		self.player1.select = unittest.mock.Mock(side_effect=[player1_kc_1_select_future, player1_kc_2_select_future, player1_kc_3_select_future, player1_kc_4_select_future])
		kc.play()
		player1_kc_1_select_future.set_result(["King's Court"])
		yield gen.moment
		player1_kc_2_select_future.set_result(["Caravan"])
		yield gen.moment
		player1_kc_3_select_future.set_result(["Caravan"])
		yield gen.moment
		player1_kc_4_select_future.set_result(["Caravan"])
		yield gen.moment
		self.assertTrue(len(self.player1.durations) == 4)
		self.assertTrue(len(self.player1.played_cards) == 1)
		self.assertTrue(len(self.player1.duration_cbs) == 12)

	@tornado.testing.gen_test
	def test_tr_tr_duration(self):
		tu.print_test_header("Test throne room throne room duration")
		tr = base.Throne_Room(self.game, self.player1)
		caravan = sea.Caravan(self.game, self.player1)
		tu.add_many_to_hand(self.player1, tr, 2)
		tu.add_many_to_hand(self.player1, caravan, 2)

		player1_tr_1_select_future = gen.Future()
		player1_tr_2_select_future = gen.Future()
		player1_tr_3_select_future = gen.Future()
		self.player1.select = unittest.mock.Mock(side_effect=[player1_tr_1_select_future, player1_tr_2_select_future, player1_tr_3_select_future])
		tr.play()
		player1_tr_1_select_future.set_result(["Throne Room"])
		yield gen.moment
		player1_tr_2_select_future.set_result(["Caravan"])
		yield gen.moment
		player1_tr_3_select_future.set_result(["Caravan"])
		yield gen.moment
		self.assertTrue(len(self.player1.durations) == 3)
		self.assertTrue(len(self.player1.played_cards) == 1)
		self.assertTrue(len(self.player1.duration_cbs) == 6)

	@tornado.testing.gen_test
	def test_throne_room_duration(self):
		tu.print_test_header("Test throne room duration end effect")
		throne_room = base.Throne_Room(self.game, self.player1)
		lighthouse = sea.Lighthouse(self.game, self.player1)
		self.player1.hand.add(throne_room)
		self.player1.hand.add(lighthouse)
		yield tu.send_input(self.player1, "play", "Throne Room")
		yield tu.send_input(self.player1, "post_selection", ["Lighthouse"])
		self.assertTrue(throne_room in self.player1.durations)
		self.assertTrue(lighthouse in self.player1.durations)
		self.assertTrue(throne_room not in self.player1.played_cards)
		self.assertTrue(lighthouse not in self.player1.played_cards)
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(self.player1.balance == 2)

		self.player1.end_turn()
		self.player2.end_turn()
		self.player3.end_turn()

		self.assertTrue(throne_room not in self.player1.durations)
		self.assertTrue(lighthouse not in self.player1.durations)
		self.assertTrue(throne_room in self.player1.played_cards)
		self.assertTrue(lighthouse in self.player1.played_cards)
		self.assertTrue(self.player1.balance == 2)

	@tornado.testing.gen_test
	def test_Kings_Court_duration(self):
		tu.print_test_header("testing King's Court Duration end effect")
		lighthouse = sea.Lighthouse(self.game, self.player1)
		kings_court = prosperity.Kings_Court(self.game, self.player1)
		tu.set_player_hand(self.player1, [lighthouse, kings_court])
		kings_court.play()
		yield tu.send_input(self.player1, "post_selection", ["Lighthouse"])
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(self.player1.balance == 3)
		self.player1.end_turn()
		self.player2.end_turn()
		self.player3.end_turn()
		self.assertTrue(kings_court not in self.player1.durations)
		self.assertTrue(lighthouse not in self.player1.durations)
		self.assertTrue(kings_court in self.player1.played_cards)
		self.assertTrue(lighthouse in self.player1.played_cards)
		self.assertTrue(self.player1.balance == 3)

if __name__ == '__main__':
	unittest.main()