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
		print ("Starting hand size ", str(base_hand_size))
		num_victory_cards = len(self.player1.hand.get_cards_by_type("Victory"))
		
		tu.send_input(self.player1, "play", "Crossroads")
		num_actions = self.player1.actions
		print ("starting vc is ", str(num_victory_cards))
		print ("The hand len after 1 cr is ", str(len(self.player1.hand)))
		print ("The hand after 1 cr is ", str(self.player1.hand.card_array()))
		self.assertTrue(num_actions == 3)
		self.assertTrue(len(self.player1.hand ) == num_victory_cards + base_hand_size - 1)
		base_hand_size = len(self.player1.hand)
		num_victory_cards = len(self.player1.hand.get_cards_by_type("Victory"))
		deck_size = len(self.player1.deck)


		tu.send_input(self.player1, "play", "Crossroads")
		self.assertTrue(self.player1.actions == num_actions - 1)
		print ("hand size after 2 cr is ", str(base_hand_size))
		print ("The hand after 2 cr is ", str(self.player1.hand.card_array()))
		print ("vc cards after 2 cr is ", str(num_victory_cards))
		expected_drawn = min(deck_size, num_victory_cards)
		self.assertTrue(len(self.player1.hand) == expected_drawn + base_hand_size - 1) 

if __name__ == '__main__':
	unittest.main()