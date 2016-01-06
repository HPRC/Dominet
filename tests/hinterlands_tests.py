import unittest
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.hinterlands as hl
import sets.prosperity as prosperity
import sets.supply as supply_cards
import game as g
import kingdomGenerator as kg

import tornado.testing
import tornado.gen as gen

import tests.test_utils as tu


class TestHinterland(tornado.testing.AsyncTestCase):
	def setUp(self):
		super().setUp()
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], kg.all_card_titles(), [], test=True)
		#hard code order of players so that random turn order doesn't interfere with tests
		self.game.players = [self.player1, self.player2, self.player3]
		for i in self.game.players:
			i.game = self.game
		self.game.start_game()
		self.player1.take_turn()


# --------------------------------------------------------
# ----------------------- Hinterlands --------------------
# --------------------------------------------------------

	def test_Crossroads(self):
		tu.print_test_header("test Crossroads")
		crossroads = hl.Crossroads(self.game, self.player1)
		tu.add_many_to_hand(self.player1, crossroads, 2)
		base_hand_size = len(self.player1.hand)
		num_victory_cards = len(self.player1.hand.get_cards_by_type("Victory"))
		
		tu.send_input(self.player1, "play", "Crossroads")
		num_actions = self.player1.actions
		self.assertTrue(num_actions == 3)
		self.assertTrue(len(self.player1.hand ) == num_victory_cards + base_hand_size - 1)
		base_hand_size = len(self.player1.hand)
		num_victory_cards = len(self.player1.hand.get_cards_by_type("Victory"))
		deck_size = len(self.player1.deck)

		tu.send_input(self.player1, "play", "Crossroads")
		self.assertTrue(self.player1.actions == num_actions - 1)
		expected_drawn = min(deck_size, num_victory_cards)
		self.assertTrue(len(self.player1.hand) == expected_drawn + base_hand_size - 1) 

	@tornado.testing.gen_test
	def test_Crossroads_Throne_Room(self):
		tu.print_test_header("test Crossroads Throne Room")
		crossroads = hl.Crossroads(self.game, self.player1)
		throneroom = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(throneroom)
		self.player1.hand.add(crossroads)
		
		tu.send_input(self.player1, "play", "Throne Room")
		yield tu.send_input(self.player1, "post_selection", ["Crossroads"])
		self.assertTrue(self.player1.actions == 3)

	@tornado.testing.gen_test
	def test_Duchess(self):
		tu.print_test_header("Test Duchess")
		duchess = hl.Duchess(self.game, self.player1)
		self.player1.hand.add(duchess)

		player1top = self.player1.deck[-1]
		player2top = self.player2.deck[-1]
		player3top = self.player3.deck[-1]

		tu.send_input(self.player1, "play", "Duchess")
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		self.assertTrue(self.player3.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Discard"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player2.discard_pile[-1] == player2top)
		self.assertTrue(self.player2.last_mode["mode"] != "select")
		yield tu.send_input(self.player1, "post_selection", ["Put back"])
		self.assertTrue(self.player1.deck[-1] == player1top)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player3, "post_selection", ["Discard"])
		self.assertTrue(self.player1.last_mode["mode"] != "wait")

		self.player1.end_turn()
		self.player2.balance = 5
		yield tu.send_input(self.player2, "buyCard", "Duchy")
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Yes"])
		self.assertTrue(self.player2.last_mode["mode"] != "select")
		self.assertTrue(self.player2.discard_pile[-1].title == "Duchess")

	@tornado.testing.gen_test
	def test_Develop(self):
		tu.print_test_header("Test Develop")
		develop = hl.Develop(self.game, self.player1)
		tu.add_many_to_hand(self.player1, develop, 2)
		self.player1.hand.add(supply_cards.Copper(self.game, self.player1))
		self.player1.hand.add(supply_cards.Estate(self.game, self.player1))

		develop.play()

		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		develop.play()
		yield tu.send_input(self.player1, "post_selection", ["Estate"])
		yield tu.send_input(self.player1, "selectSupply", ["Silver"])
		self.assertTrue("Silver" == self.player1.discard_pile[-1].title)



	@tornado.testing.gen_test
	def test_Duchess_Feast(self):
		tu.print_test_header("Test Duchess Feast")
		feast = base.Feast(self.game, self.player1)
		self.player1.hand.add(feast)

		tu.send_input(self.player1, "play", "Feast")
		yield tu.send_input(self.player1, "post_selection", ["Duchy"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Duchess")

	@tornado.testing.gen_test
	def test_Trader(self):
		tu.print_test_header("test Trader")
		witch = base.Witch(self.game, self.player1)
		trader = hl.Trader(self.game, self.player2)

		self.player1.hand.add(witch)
		self.player2.hand.add(trader)
		#reaction
		tu.send_input(self.player1, "play", "Witch")
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		yield tu.send_input(self.player2, "post_selection", ["Hide"])
		#workaround for heavily nested coroutines not finishing before test occur causing failure
		yield gen.sleep(.2)
		self.assertTrue(len(self.game.trash_pile) == 0)
		#and gained a silver
		self.assertTrue(self.player2.discard_pile[-1].title == "Silver")
		self.assertTrue(self.player1.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.discard_pile[-1].title == "Curse")
		self.assertTrue(self.game.supply.get_count("Curse") == 19)

		self.player1.end_turn()

		self.player2.hand.add(supply_cards.Estate(self.game, self.player2))
		tu.send_input(self.player2, "play", "Trader")
		yield tu.send_input(self.player2, "post_selection", ["Estate"])
		self.assertTrue(len(self.player2.discard_pile) == 3)

	@tornado.testing.gen_test
	def test_Nomad_Camp(self):
		tu.print_test_header("test Nomad Camp")
		self.player1.hand.add(base.Workshop(self.game, self.player1))
		yield tu.send_input(self.player1, "play", "Workshop")
		yield tu.send_input(self.player1, "post_selection", ["Nomad Camp"])
		self.assertTrue(self.player1.deck[-1].title == "Nomad Camp")

	@tornado.testing.gen_test
	def test_Mandarin(self):
		tu.print_test_header("test Mandarin")
		tu.add_many_to_hand(self.player1, supply_cards.Silver(self.game, self.player1), 3)
		tu.add_many_to_hand(self.player1, supply_cards.Gold(self.game, self.player1), 2)

		tu.send_input(self.player1, "play", "Gold")
		tu.send_input(self.player1, "play", "Silver")
		tu.send_input(self.player1, "play", "Silver")

		yield tu.send_input(self.player1, "buyCard", "Mandarin")
		
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Silver", "Silver", "Gold"])
		self.assertTrue(len(self.player1.played_cards) == 0)
		self.assertTrue(self.player1.deck[-1].title == "Gold")
		self.assertTrue(self.player1.deck[-2].title == "Silver")
		self.assertTrue(self.player1.deck[-3].title == "Silver")

		self.player1.end_turn()
		self.player2.hand.add(hl.Mandarin(self.game, self.player2))
		self.player2.hand.add(supply_cards.Silver(self.game, self.player2))
		tu.send_input(self.player2, "play", "Mandarin")
		self.assertTrue(self.player2.balance == 3)
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Copper"])
		self.assertTrue(self.player2.deck[-1].title == "Copper")
		self.assertTrue(len(self.player2.hand) == 5)

	@tornado.testing.gen_test
	def test_duchess_watchtower(self):
		tu.print_test_header("test Duchess Watchtower")
		feast = base.Feast(self.game, self.player1)
		watchtower = prosperity.Watchtower(self.game, self.player1)
		self.player1.hand.add(watchtower)
		self.player1.hand.add(feast)

		tu.send_input(self.player1, "play", "Feast")
		yield tu.send_input(self.player1, "selectSupply", ["Duchy"])
		#choose to gain the duchess
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Duchess")
		#choose to reveal Watchtower
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])

		self.assertTrue(self.player1.deck[-1].title == "Duchess")
		yield tu.send_input(self.player1, "post_selection", ["Hide"])

	@tornado.testing.gen_test
	def test_watchtower_trader(self):
		tu.print_test_header("test Watchtower Trader")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		trader = hl.Trader(self.game, self.player1)
		self.player1.hand.add(watchtower)
		self.player1.hand.add(trader)

		self.player1.spend_all_money()
		yield tu.send_input(self.player1, "buyCard", "Copper")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		#order reactions, reveal trader then watchtower
		yield tu.send_input(self.player1, "post_selection", ["Watchtower", "Trader"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		#reveal trader
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		self.assertTrue(self.game.supply.get_count("Copper") == 30)
		#gaining silver now

		yield tu.send_input(self.player1, "post_selection", ["Watchtower", "Trader"])
		yield tu.send_input(self.player1, "post_selection", ["Hide"])
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")

		#watchtower from the copper earlier
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")

	@tornado.testing.gen_test
	def test_trader_royal_seal(self):
		tu.print_test_header("test Royal Seal Trader")
		royal_seal = prosperity.Royal_Seal(self.game, self.player1)
		trader = hl.Trader(self.game, self.player1)
		self.player1.hand.add(royal_seal)
		self.player1.hand.add(trader)

		royal_seal.play()
		yield tu.send_input(self.player1, "buyCard", "Copper")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		self.assertTrue(self.game.get_turn_owner() == self.player1)

		self.assertTrue(self.player1.last_mode["mode"] == "select")
		# trader triggers again for the new silver
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield gen.sleep(.1)
		# royal seal triggers
		self.assertTrue(self.game.get_turn_owner() == self.player1)
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")

	@tornado.testing.gen_test
	def test_Cache(self):
		tu.print_test_header("test Cache")
		yield tu.send_input(self.player1, "buyCard", "Cache")
		self.assertTrue(len(self.player1.discard_pile) == 3)
		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Cache"]) == 1)
		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Copper"]) == 2)

	@tornado.testing.gen_test
	def test_Ill_Gotten_Gains(self):
		tu.print_test_header("test Ill-Gotten Gains")
		ill_gotten_gains = hl.Ill_Gotten_Gains(self.game, self.player1)
		self.player1.hand.add(ill_gotten_gains)

		yield tu.send_input(self.player1, "buyCard", "Ill Gotten Gains")
		self.assertTrue(len([x for x in self.player2.discard_pile if x.title == "Curse"]) == 1)
		self.assertTrue(len([x for x in self.player3.discard_pile if x.title == "Curse"]) == 1)

		ill_gotten_gains.play()

		yield tu.send_input(self.player1, "post_selection", ["Yes"])

		self.assertTrue(len(self.player1.hand) == 6)






if __name__ == '__main__':
	unittest.main()