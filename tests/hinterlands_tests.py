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
		self.game = g.DmGame([self.player1, self.player2, self.player3], kg.all_card_titles(), [])
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

	def test_Trader(self):
		tu.print_test_header("test Trader")
		witch = base.Witch(self.game, self.player1)
		trader = hl.Trader(self.game, self.player2)

		self.player1.hand.add(witch)
		self.player2.hand.add(trader)
		#reaction
		tu.send_input(self.player1, "play", "Witch")
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		tu.send_input(self.player2, "post_selection", ["Reveal"])
		#should have trashed curse from witch
		self.assertTrue(self.game.trash_pile[-1].title == "Curse")
		#and gained a silver
		self.assertTrue(self.player2.discard_pile[-1].title == "Silver")
		self.assertTrue(self.player1.last_mode["mode"] != "wait")
		self.player1.end_turn()

		self.player2.hand.add(crd.Estate(self.game, self.player2))
		tu.send_input(self.player2, "play", "Trader")
		tu.send_input(self.player2, "post_selection", ["Estate"])
		self.assertTrue(len(self.player2.discard_pile) == 3)


if __name__ == '__main__':
	unittest.main()