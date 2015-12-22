import unittest
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.hinterlands as hl
import sets.card as crd
import game as g
import kingdomGenerator as kg

import tests.test_utils as tu


class TestHinterland(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], kg.all_card_titles(), [], test=True)
		# hard code order of players so that random turn order doesn't interfere with tests
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
		tu.send_input(self.player2, "post_selection", ["Discard"])
		self.assertTrue(self.player2.discard_pile[-1] == player2top)
		self.assertTrue(self.player2.last_mode["mode"] != "select")
		tu.send_input(self.player1, "post_selection", ["Put back"])
		self.assertTrue(self.player1.deck[-1] == player1top)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		tu.send_input(self.player3, "post_selection", ["Discard"])
		self.assertTrue(self.player1.last_mode["mode"] != "wait")

		self.player1.end_turn()
		self.player2.balance = 5
		tu.send_input(self.player2, "buyCard", "Duchy")
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		tu.send_input(self.player2, "post_selection", ["Yes"])
		self.assertTrue(self.player2.last_mode["mode"] != "select")
		self.assertTrue(self.player2.discard_pile[-1].title == "Duchess")

	def test_Trader(self):
		tu.print_test_header("test Trader")
		witch = base.Witch(self.game, self.player1)
		trader = hl.Trader(self.game, self.player2)

		self.player1.hand.add(witch)
		self.player2.hand.add(trader)
		# reaction
		tu.send_input(self.player1, "play", "Witch")
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		tu.send_input(self.player2, "post_selection", ["Reveal"])
		# no curse from witch
		self.assertTrue(len(self.game.trash_pile) == 0)
		self.assertTrue(self.game.supply.get_count("Curse") == 20)
		# and gained a silver
		self.assertTrue(self.player2.discard_pile[-1].title == "Silver")
		self.assertTrue(self.player1.last_mode["mode"] != "wait")
		self.player1.end_turn()

		self.player2.hand.add(crd.Estate(self.game, self.player2))
		tu.send_input(self.player2, "play", "Trader")
		tu.send_input(self.player2, "post_selection", ["Estate"])
		self.assertTrue(len(self.player2.discard_pile) == 3)

	def test_Nomad_Camp(self):
		tu.print_test_header("test Nomad Camp")
		self.player1.hand.add(base.Workshop(self.game, self.player1))
		tu.send_input(self.player1, "play", "Workshop")
		tu.send_input(self.player1, "post_selection", ["Nomad Camp"])
		
		self.assertTrue(self.player1.deck[-1].title == "Nomad Camp")

	def test_Mandarin(self):
		tu.print_test_header("test Mandarin")
		tu.add_many_to_hand(self.player1, crd.Silver(self.game, self.player1), 3)
		tu.add_many_to_hand(self.player1, crd.Gold(self.game, self.player1), 2)

		tu.send_input(self.player1, "play", "Gold")
		tu.send_input(self.player1, "play", "Silver")
		tu.send_input(self.player1, "play", "Silver")

		tu.send_input(self.player1, "buyCard", "Mandarin")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		tu.send_input(self.player1, "post_selection", ["Silver", "Silver", "Gold"])
		self.assertTrue(len(self.player1.played) == 0)
		self.assertTrue(self.player1.deck[-1].title == "Gold")
		self.assertTrue(self.player1.deck[-2].title == "Silver")
		self.assertTrue(self.player1.deck[-3].title == "Silver")

		self.player1.end_turn()
		self.player2.hand.add(hl.Mandarin(self.game, self.player2))
		self.player2.hand.add(crd.Silver(self.game, self.player2))
		tu.send_input(self.player2, "play", "Mandarin")
		self.assertTrue(self.player2.balance == 3)
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		tu.send_input(self.player2, "post_selection", ["Copper"])
		self.assertTrue(self.player2.deck[-1].title == "Copper")
		self.assertTrue(len(self.player2.hand) == 5)

	def test_Oasis(self):
		tu.print_test_header("test Oasis")
		tu.add_many_to_hand(self.player1,)

		tu.send_input(self.player1, "play", "Oasis")

if __name__ == '__main__':
	unittest.main()