import unittest
import client as c
import card as crd
import game as g

class Player1Handler():
	log = []
	def write_json(self, **kwargs):
		if (kwargs["command"] != "announce"):
			Player1Handler.log.append(kwargs)

class Player2Handler():
	log = []
	def write_json(self, **kwargs):
		if (kwargs["command"] != "announce"):
			Player2Handler.log.append(kwargs)

class TestCard(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, Player1Handler())
		self.player2 = c.DmClient("player2", 1, Player2Handler())
		self.game = g.DmGame([self.player1, self.player2])
		for i in self.game.players:
			i.game = self.game
			i.setup()
		self.player1.take_turn()
		Player1Handler.log = []
		Player2Handler.log = []

	def test_Cellar(self):
		self.player1.hand["Cellar"] = [crd.Cellar(self.game, self.player1) ,1]
		self.player1.hand["Cellar"][0].play()
		self.assertTrue(Player1Handler.log[0]["command"] == "updateMode")
		self.assertTrue(Player1Handler.log[0]["mode"] == "select")
		self.assertTrue(self.player1.waiting["cb"] != None)

		selection = self.player1.card_list_to_titles(self.player1.hand_array())
		self.player1.waiting["cb"](selection)
		self.assertTrue(len(self.player1.discard_pile) == 5)

	def test_Militia(self):
		self.player1.hand["Militia"] = [crd.Militia(self.game, self.player1) ,1]
		self.player1.hand["Militia"][0].play()
		self.assertTrue(Player2Handler.log[0]["command"] == "updateMode")
		self.assertTrue(Player2Handler.log[0]["mode"] == "select")
		self.assertTrue(Player2Handler.log[0]["select_from"] == self.player2.card_list_to_titles(self.player2.hand_array()))
		self.assertTrue(self.player2.waiting["cb"] != None)

		selection = self.player2.card_list_to_titles(self.player2.hand_array())[:2]
		self.player2.waiting["cb"](selection)
		self.assertTrue(len(self.player2.hand_array()) == 3)

	def test_Moat_reaction(self):
		self.player2.hand["Moat"] = [crd.Moat(self.game, self.player2) ,1]
		self.player1.hand["Witch"] = [crd.Witch(self.game, self.player1) ,1]
		self.player1.hand["Witch"][0].play()
		self.assertTrue("Reveal" in Player2Handler.log[0]["select_from"])
		self.player2.waiting["cb"](["Reveal"])
		#didn't gain curse
		self.assertTrue(len(self.player2.discard_pile) == 0)
		
if __name__ == '__main__':
	unittest.main()