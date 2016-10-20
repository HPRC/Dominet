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
	def test_Cellar(self):
		tu.print_test_header("test Cellar")
		
		selection_future = gen.Future()
		select_mock = unittest.mock.MagicMock(return_value=selection_future)
		draw_mock = unittest.mock.Mock()
		discard_mock = unittest.mock.Mock()
		self.player1.select = select_mock
		self.player1.draw = draw_mock
		self.player1.discard = gen.coroutine(discard_mock)
		
		base.Cellar(self.game, self.player1).play()

		self.assertTrue(select_mock.called)
		to_discard = crd.card_list_to_titles(self.player1.hand.card_array())
		selection_future.set_result(to_discard)
		yield gen.moment
		discard_mock.assert_any_call(to_discard, self.player1.discard_pile)
		draw_mock.assert_called_once_with(5)

	@tornado.testing.gen_test
	def test_Militia(self):
		tu.print_test_header("test Militia")

		player2_discard_future = gen.Future()
		player3_discard_future = gen.Future()
		select_mock2 = unittest.mock.MagicMock(return_value=player2_discard_future)
		select_mock3 = unittest.mock.MagicMock(return_value=player3_discard_future)
		discard_mock2 =unittest.mock.Mock()
		discard_mock3 =unittest.mock.Mock()

		self.player2.select = select_mock2
		self.player3.select = select_mock3
		self.player2.discard = gen.coroutine(discard_mock2)
		self.player3.discard = gen.coroutine(discard_mock3)

		base.Militia(self.game, self.player1).play()
		self.assertTrue(select_mock2.called)
		self.assertTrue(select_mock3.called)
		select_mock2.assert_called_with(unittest.mock.ANY, unittest.mock.ANY, 
			crd.card_list_to_titles(self.player2.hand.card_array()), unittest.mock.ANY)

		player2_selection = crd.card_list_to_titles(self.player2.hand.card_array())[:2]
		player2_discard_future.set_result(player2_selection)
		yield gen.moment
		discard_mock2.assert_called_once_with(player2_selection, self.player2.discard_pile)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		player3_selection = ["Copper", "Copper"]
		player3_discard_future.set_result(player3_selection)
		yield gen.moment
		discard_mock3.assert_called_once_with(player3_selection, self.player3.discard_pile)

	@tornado.testing.gen_test
	def test_Moat_reaction(self):
		tu.print_test_header("test Moat Reaction")
		moat = base.Moat(self.game, self.player2)
		self.player2.hand.add(moat)
		moat.react = unittest.mock.Mock(moat, wraps=moat.react)
		self.player2.gain = unittest.mock.Mock()

		reveal_future = gen.Future()
		reveal_mock = unittest.mock.MagicMock(return_value=reveal_future)
		self.player2.select = reveal_mock
		base.Witch(self.game, self.player1).play()
		self.assertTrue(moat.react.called)
		reveal_future.set_result(["Reveal"])
		yield gen.moment
		self.assertTrue(self.player2.protection == 1)
		self.assertFalse(self.player2.gain.called)
		self.assertTrue(self.player2.search_and_extract_card("Curse") == None)

	@tornado.testing.gen_test
	def test_Throne_Room_on_Village(self):
		tu.print_test_header("test Throne Room Village")
		throne_room_card = base.Throne_Room(self.game, self.player1)
		village = base.Village(self.game, self.player1)
		self.player1.hand.add(throne_room_card)
		self.player1.hand.add(village)
		
		village.play = unittest.mock.Mock()
		select_future = gen.Future()
		throne_room_selection = unittest.mock.MagicMock(return_value=select_future)
		
		self.player1.select = throne_room_selection

		throne_room_card.play()
		select_future.set_result(["Village"])
		yield gen.moment
		village.play.assert_called_with(True)
		self.assertTrue(village.play.call_count == 2)

	@tornado.testing.gen_test
	def test_Throne_Room_on_Workshop(self):
		tu.print_test_header("test Throne Room workshop")
		throne_room = base.Throne_Room(self.game, self.player1)
		workshop = base.Workshop(self.game, self.player1)
		self.player1.hand.add(workshop)
		self.player1.hand.add(throne_room)

		select_future = gen.Future()
		select_from_supply_future = gen.Future()
		select_from_supply_future2 = gen.Future()
		self.player1.select = unittest.mock.MagicMock(return_value=select_future)
		self.player1.select_from_supply = unittest.mock.MagicMock(side_effect=[select_from_supply_future, select_from_supply_future2])
		self.player1.gain = unittest.mock.Mock(wraps=self.player1.gain)

		throne_room.play()
		select_future.set_result(["Workshop"])
		yield gen.moment

		select_from_supply_future.set_result(["Silver"])
		yield gen.moment
		self.player1.gain.assert_called_once_with("Silver")

		select_from_supply_future2.set_result(["Estate"])
		yield gen.moment
		self.player1.gain.assert_called_with("Estate")

	@tornado.testing.gen_test
	def test_Feast(self):
		tu.print_test_header("test Feast")
		feast_card = base.Feast(self.game, self.player1)
		self.player1.hand.add(feast_card)
		select_future = gen.Future()
		self.player1.select_from_supply = unittest.mock.MagicMock(return_value=select_future)
		self.player1.gain = unittest.mock.Mock(return_value = gen.Future())
		feast_card.play()
		select_future.set_result(["Duchy"])
		yield gen.moment
		self.assertTrue(self.game.trash_pile[-1] == feast_card)
		self.player1.gain.assert_called_with("Duchy")

	@tornado.testing.gen_test
	def test_Thief_2_treasures(self):
		tu.print_test_header("test Thief on 2 treasures")
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand.add(thief_card)
		self.player2.deck.append(supply_cards.Copper(self.game, self.player2))
		self.player2.deck.append(supply_cards.Silver(self.game, self.player2))
		select_trash_future = gen.Future()
		select_gain_future = gen.Future()
		self.player1.select = unittest.mock.MagicMock(side_effect=[select_trash_future, select_gain_future])
		self.player1.gain = unittest.mock.Mock(return_value=gen.Future())

		thief_card.play()

		self.player1.select.assert_called_with(1, 1, ["Silver", "Copper"], unittest.mock.ANY)
		select_trash_future.set_result(["Silver"])
		yield gen.moment
		self.assertTrue(self.game.trash_pile[-1].title == "Silver")
		select_gain_future.set_result(["Yes"])
		yield gen.moment
		self.player1.gain.assert_called_with("Silver", False)

	@tornado.testing.gen_test
	def test_Thief_1_treasure(self):
		tu.print_test_header("test Thief on 1 treasure")
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand.add(thief_card)
		self.player2.deck.append(supply_cards.Estate(self.game, self.player2))
		self.player2.deck.append(supply_cards.Gold(self.game, self.player2))
		select_gain_future = gen.Future()
		self.player1.select = unittest.mock.MagicMock(return_value=select_gain_future)
		self.player1.gain = unittest.mock.Mock(return_value=gen.Future())
		thief_card.play()
		self.assertTrue(self.game.trash_pile[-1].title == "Gold")
		select_gain_future.set_result(["Yes"])
		yield gen.moment
		self.player1.gain.assert_called_with("Gold", False)

	@tornado.testing.gen_test
	def test_Thief_3_players(self):
		tu.print_test_header("test Thief 3 players")
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand.add(thief_card)

		player2gold = supply_cards.Gold(self.game, self.player2)
		player3copper = supply_cards.Copper(self.game, self.player3)

		self.player2.deck = [supply_cards.Estate(self.game, self.player2), player2gold]
		self.player3.deck = [player3copper, supply_cards.Estate(self.game, self.player3)]
		select_gain_gold_future = gen.Future()
		select_gain_copper_future = gen.Future()
		gain_future = gen.Future()
		self.player1.select = unittest.mock.MagicMock(side_effect=[select_gain_gold_future, select_gain_copper_future])
		self.player1.gain = unittest.mock.Mock(return_value=gain_future)

		thief_card.play()
		self.assertTrue(player2gold in self.game.trash_pile)

		select_gain_gold_future.set_result(["Yes"])
		yield gen.moment
		self.player1.gain.assert_called_with("Gold", False)
		gain_future.set_result("finish gaining gold")
		yield gen.moment
		self.assertTrue(player3copper in self.game.trash_pile)
		select_gain_copper_future.set_result(["Yes"])
		yield gen.moment
		self.player1.gain.assert_called_with("Copper", False)

	def test_Gardens(self):
		tu.print_test_header("test Gardens")
		gardens = base.Gardens(self.game, self.player1)
		self.player1.hand.add(gardens)
		self.assertTrue(gardens.get_vp() == 1)
		for i in range(0, 9):
			self.player1.deck.append(base.Gardens(self.game, self.player1))
		# decksize = 20
		self.assertTrue(self.player1.total_vp() == 23)
		self.player1.deck.append(supply_cards.Copper(self.game, self.player1))
		self.assertTrue(self.player1.total_vp() == 23)

	@tornado.testing.gen_test
	def test_Chancellor(self):
		tu.print_test_header("test Chancellor")
		self.player1.discard_pile.append(supply_cards.Copper(self.game, self.player1))
		chancellor = base.Chancellor(self.game, self.player1)
		self.player1.hand.add(chancellor)
		select_future = gen.Future()
		self.player1.select = unittest.mock.Mock(return_value=select_future)
		chancellor.play()
		self.assertTrue(len(self.player1.discard_pile) == 1)
		decksize = len(self.player1.deck)
		select_future.set_result(["Yes"])
		yield gen.moment
		self.assertTrue(len(self.player1.discard_pile) == decksize + 1)
		self.assertTrue(len(self.player1.deck) == 0)

	def test_Adventurer(self):
		tu.print_test_header("test Adventurer")
		estate = supply_cards.Estate(self.game, self.player1)
		gold = supply_cards.Gold(self.game, self.player1)
		adventurer = base.Adventurer(self.game, self.player1)
		self.player1.deck = [estate, estate, estate]
		self.player1.discard_pile = [gold, gold]

		self.player1.hand.add(adventurer)
		adventurer.play()
		self.assertTrue(self.player1.hand.get_count("Gold") == 2)
		self.assertTrue(len(self.player1.deck) == 0)
		self.assertTrue(len(self.player1.discard_pile) == 3)

	def test_Adventurer_empty_deck(self):
		tu.print_test_header("test Adventurer")
		estate = supply_cards.Estate(self.game, self.player1)
		gold = supply_cards.Gold(self.game, self.player1)
		adventurer = base.Adventurer(self.game, self.player1)
		self.player1.deck = []
		self.player1.discard_pile = [gold]

		self.player1.hand.add(adventurer)
		adventurer.play()
		self.assertTrue(self.player1.hand.get_count("Gold") == 1)
		self.assertTrue(len(self.player1.deck) == 0)
		self.assertTrue(len(self.player1.discard_pile) == 0)

	@tornado.testing.gen_test
	def test_Library(self):
		tu.print_test_header("test Library")
		library = base.Library(self.game, self.player1)
		village = base.Village(self.game, self.player1)
		copper = supply_cards.Copper(self.game, self.player1)
		self.player1.deck = [copper, village, copper]
		self.player1.hand.add(library)
		self.player1.hand.add = unittest.mock.Mock()
		select_future = gen.Future()
		self.player1.select = unittest.mock.Mock(return_value=select_future)
		library.play()
		self.player1.hand.add.assert_called_with(copper)
		select_future.set_result(["Yes"])
		yield gen.moment
		self.player1.hand.add.assert_called_with(copper)
		self.assertTrue("Village" not in self.player1.hand)

	@tornado.testing.gen_test
	def test_Witch(self):
		tu.print_test_header("test Witch")
		witch = base.Witch(self.game, self.player1)
		player_2_gain_curse_future = gen.Future()
		self.player2.gain = unittest.mock.Mock(return_value=player_2_gain_curse_future)
		self.player3.gain = unittest.mock.Mock(return_value=gen.Future())
		witch.play()
		self.player2.gain.assert_called_with("Curse")
		player_2_gain_curse_future.set_result("done gaining curse")
		yield gen.moment
		self.player3.gain.assert_called_with("Curse")
		self.assertTrue(self.player1.last_mode["mode"] != "wait")

	@tornado.testing.gen_test
	def test_2_Reactions(self):
		tu.print_test_header("test 2 reaction secret chamber moat")
		militia = base.Militia(self.game, self.player1)
		moat = base.Moat(self.game, self.player2)
		secret_chamber = intrigue.Secret_Chamber(self.game, self.player2)
		estate = supply_cards.Estate(self.game, self.player2)
		self.player2.hand.add(moat)
		self.player2.hand.add(secret_chamber)
		self.player2.deck.append(estate)
		self.player2.deck.append(estate)
		moat3 = base.Moat(self.game, self.player3)
		secret_chamber3 = intrigue.Secret_Chamber(self.game, self.player3)
		silver = supply_cards.Silver(self.game, self.player3)
		tu.set_player_hand(self.player3, [silver, silver, silver, moat3, secret_chamber3])

		militia.play()
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		self.assertTrue("Secret Chamber" in self.player2.last_mode["select_from"])		
		self.assertTrue("Moat" in self.player2.last_mode["select_from"])
		yield tu.send_input(self.player2, "post_selection", ["Secret Chamber", "Moat"])
		#moat trigger first
		self.assertTrue("Moat" in self.player2.last_mode["msg"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")

		#while player2 is deciding to reveal moat or not,
		#player3 chose order Secret chamber first
		self.assertTrue(self.player3.last_mode["mode"] == "select")

		yield tu.send_input(self.player3, "post_selection", ["Moat", "Secret Chamber"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")

		#player3 reveals secret chamber
		self.assertTrue("Secret Chamber" in self.player3.last_mode["msg"])
		yield tu.send_input(self.player3, "post_selection", ["Reveal"])

		#player3 chooses to put back secret chamber and moat in secret chamber reaction
		yield tu.send_input(self.player3, "post_selection", ["Secret Chamber", "Moat"])
		self.assertTrue(self.player3.deck[-1].title == "Moat")
		self.assertTrue(self.player3.deck[-2].title == "Secret Chamber")
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		#player2 reveals moat
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		#player2 reveals secret chamber
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		#player2 puts back Estate, moat
		self.assertTrue(self.player2.protection == 1)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player2, "post_selection", ["Moat", "Estate"])
		self.assertTrue(self.player2.deck[-1].title == "Estate")
		self.assertTrue(self.player2.deck[-2].title == "Moat")
		#workaround to allow ioloop to process nested yields in time
		yield gen.sleep(.2)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		#player3 discards 2 silver
		yield tu.send_input(self.player3, "post_selection", ["Silver", "Silver"])
		self.assertTrue(len(self.player3.hand)==3)
		#player1 resumes
		self.assertTrue(self.player1.last_mode["mode"] == "buy")

	@tornado.testing.gen_test
	def test_2_reaction_waits(self):
		tu.print_test_header("test 2 reaction waits")
		militia = base.Militia(self.game, self.player1)
		moat = base.Moat(self.game, self.player2)
		secret_chamber = intrigue.Secret_Chamber(self.game, self.player2)
		self.player2.hand.add(moat)
		self.player2.hand.add(secret_chamber)
		self.player2.deck.append(supply_cards.Estate(self.game, self.player2))
		self.player2.deck.append(supply_cards.Estate(self.game, self.player2))

		moat3 = base.Moat(self.game, self.player3)
		secret_chamber3 = intrigue.Secret_Chamber(self.game, self.player3)
		silver = supply_cards.Silver(self.game, self.player3)
		tu.set_player_hand(self.player3, [silver, silver, silver, moat3, secret_chamber3])

		militia.play()
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 choose order, moat then secret chamber
		yield tu.send_input(self.player2, "post_selection", ["Secret Chamber", "Moat"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 reveals moat
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 3 chooses same order, moat then secret chamber
		yield tu.send_input(self.player3, "post_selection", ["Secret Chamber", "Moat"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 reveals secret chamber
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 draws 2 estates, puts back 1 and a copper
		yield tu.send_input(self.player2, "post_selection", ["Estate", "Copper"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 3 reveals moat
		yield tu.send_input(self.player3, "post_selection", ["Reveal"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 3 hides secret chamber
		yield tu.send_input(self.player3, "post_selection", ["Hide"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 drew cards so is reprompted and chooses order again
		yield tu.send_input(self.player2, "post_selection", ["Secret Chamber", "Moat"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 hides moat
		yield tu.send_input(self.player2, "post_selection", ["Hide"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		#player 2 hides secret chamber
		yield tu.send_input(self.player2, "post_selection", ["Hide"])
		yield gen.sleep(.1)
		self.assertTrue(self.player1.last_mode["mode"] != "wait")


	@tornado.testing.gen_test
	def test_throne_room_throne_room(self):
		tu.print_test_header("Test throne room throne room")
		throneroom = base.Throne_Room(self.game, self.player1)
		throneroom2 = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(throneroom)
		self.player1.hand.add(throneroom2)
		yield tu.send_input(self.player1, "play", "Throne Room")
		yield tu.send_input(self.player1, "post_selection", ["Throne Room"])

		self.player1.end_turn()
		self.player2.end_turn()
		self.player3.end_turn()

		self.player1.hand.add(throneroom)
		self.player1.hand.add(throneroom2)
		self.player1.hand.add(base.Village(self.game, self.player1))
		self.player1.hand.add(base.Village(self.game, self.player1))
		self.player1.hand.add(base.Woodcutter(self.game, self.player1))
		yield tu.send_input(self.player1, "play", "Throne Room")
		yield tu.send_input(self.player1, "post_selection", ["Village"])
		self.assertTrue(self.player1.actions == 4)
		self.assertTrue(self.player1.last_mode["mode"] == "action")

		yield tu.send_input(self.player1, "play", "Throne Room")
		yield tu.send_input(self.player1, "post_selection", ["Woodcutter"])
		self.assertTrue(self.player1.balance == 4)
		self.assertTrue(self.player1.last_mode["mode"] == "action")

	@tornado.testing.gen_test
	def test_throne_room_duration(self):
		tu.print_test_header("Test throne room duration")
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

if __name__ == '__main__':
	unittest.main()