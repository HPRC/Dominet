import unittest
import client as c
import base_set as base
import card as crd
import game as g
import kingdomGenerator as kg

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
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for i in self.game.players:
			i.game = self.game
			i.setup()
		self.player1.take_turn()
		Player1Handler.log = []
		Player2Handler.log = []

	def test_Cellar(self):
		self.player1.hand["Cellar"] = [base.Cellar(self.game, self.player1) ,1]
		self.player1.hand["Cellar"][0].play()
		self.assertTrue(Player1Handler.log[0]["command"] == "updateMode")
		self.assertTrue(Player1Handler.log[0]["mode"] == "select")
		self.assertTrue(self.player1.waiting["cb"] != None)

		selection = self.player1.card_list_to_titles(self.player1.hand_array())
		self.player1.waiting["cb"](selection)
		self.assertTrue(len(self.player1.discard_pile) == 5)

	def test_Militia(self):
		self.player1.hand["Militia"] = [base.Militia(self.game, self.player1) ,1]
		self.player1.hand["Militia"][0].play()
		self.assertTrue(Player2Handler.log[0]["command"] == "updateMode")
		self.assertTrue(Player2Handler.log[0]["mode"] == "select")
		self.assertTrue(Player2Handler.log[0]["select_from"] == self.player2.card_list_to_titles(self.player2.hand_array()))
		self.assertTrue(self.player2.waiting["cb"] != None)

		selection = self.player2.card_list_to_titles(self.player2.hand_array())[:2]
		self.player2.waiting["cb"](selection)
		self.assertTrue(len(self.player2.hand_array()) == 3)

	def test_Moat_reaction(self):
		self.player2.hand["Moat"] = [base.Moat(self.game, self.player2) ,1]
		self.player1.hand["Witch"] = [base.Witch(self.game, self.player1) ,1]
		self.player1.hand["Witch"][0].play()
		self.assertTrue("Reveal" in Player2Handler.log[0]["select_from"])
		self.player2.waiting["cb"](["Reveal"])
		#didn't gain curse
		self.assertTrue(len(self.player2.discard_pile) == 0)
		
	def test_Throne_Room_on_Village(self):
		throne_room_card = base.Throne_Room(self.game, self.player1)
		self.player1.hand["Throne Room"] = [throne_room_card ,1]
		self.player1.hand["Village"] = [base.Village(self.game, self.player1) ,1]
		throne_room_card.play()
		self.assertTrue(Player1Handler.log[0]["select_from"] == ["Village"])
		throne_room_card.post_select(["Village"])
		self.assertTrue(self.player1.actions == 4)

	def test_Throne_Room_on_Workshop(self):
		throne_room_card = base.Throne_Room(self.game, self.player1)
		self.player1.hand["Throne Room"] = [throne_room_card ,1]
		workshopCard = base.Workshop(self.game, self.player1)
		self.player1.hand["Workshop"] = [workshopCard ,1]
		throne_room_card.play()
		throne_room_card.post_select(["Workshop"])
		self.assertTrue(workshopCard.done.__name__ == "second_play")
		
		self.player1.update_wait()
		self.player1.waiting["cb"]("Silver")
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")
		self.assertTrue(workshopCard.done.__name__ == "final_done")

		self.player1.update_wait()
		self.player1.waiting["cb"]("Estate")
		self.assertTrue(self.player1.discard_pile[-1].title == "Estate")

	def test_Feast(self):
		feast_card = base.Feast(self.game, self.player1)
		self.player1.hand["Feast"] = [feast_card ,1]
		feast_card.play()

		self.assertTrue(Player1Handler.log[-1]["mode"] == "gain")
		self.assertTrue(self.player1.trash_pile[-1] == feast_card)

	def test_Thief_2_treasures(self):
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand["Thief"] = [thief_card ,1]
		self.player2.deck.append(crd.Copper(self.game, self.player2))
		self.player2.deck.append(crd.Silver(self.game, self.player2))
		thief_card.play()
		self.assertTrue("Copper" in Player1Handler.log[-1]['select_from'])
		self.assertTrue("Silver" in Player1Handler.log[-1]['select_from'])
		self.player1.waiting["cb"](["Silver"])
		self.assertTrue(self.player2.trash_pile[-1].title == "Silver")
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")

	def test_Thief_1_treasure(self):
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand["Thief"] = [thief_card ,1]
		self.player2.deck.append(crd.Estate(self.game, self.player2))
		self.player2.deck.append(crd.Gold(self.game, self.player2))
		thief_card.play()
		self.assertTrue(self.player2.trash_pile[-1].title == "Gold")
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Gold")

	def test_Gardens(self):
		gardens = base.Gardens(self.game, self.player1)
		self.player1.hand["Gardens"] = [gardens, 1]
		self.assertTrue(gardens.get_vp() == 1)
		for i in range(0,9):
			self.player1.deck.append(base.Gardens(self.game, self.player1))
		#decksize = 20
		self.assertTrue(self.player1.total_vp() == 23)
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.assertTrue(self.player1.total_vp() == 23)

	def test_Chancellor(self):
		self.player1.discard_pile.append(crd.Copper(self.game, self.player1))
		chancellor = base.Chancellor(self.game, self.player1)
		self.player1.hand["Chancellor"] = [chancellor, 1]
		chancellor.play()
		self.assertTrue(Player1Handler.log[-1]["command"] == "updateMode")
		self.assertTrue(len(self.player1.discard_pile) == 1)
		decksize = len(self.player1.deck)
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(len(self.player1.discard_pile) == 0)
		self.assertTrue(len(self.player1.deck) == decksize + 1)

	def test_Adventurer(self):
		estate = crd.Estate(self.game, self.player1)
		gold = crd.Gold(self.game, self.player1)
		adventurer = base.Adventurer(self.game, self.player1)
		self.player1.deck = [estate, estate, estate]
		self.player1.discard_pile = [gold, gold]

		self.player1.hand["Adventurer"] = [adventurer, 1]
		adventurer.play()
		self.assertTrue(self.player1.hand["Gold"][1] == 2)
		self.assertTrue(len(self.player1.deck) == 0)
		self.assertTrue(len(self.player1.discard_pile) == 3)

	def test_Library(self):
		library = base.Library(self.game, self.player1)
		village = base.Village(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.deck = [copper, village, copper]
		self.player1.hand["Library"] = [library, 1]
		library.play()
		self.assertTrue(len(self.player1.hand_array()) == 6)
		self.assertTrue(Player1Handler.log[-1]["command"] == "updateMode")
		self.player1.waiting["cb"]("Yes")
		self.assertTrue(len(self.player1.hand_array()) == 7)
		self.assertTrue(self.player1.discard_pile[-1] == village)

if __name__ == '__main__':
	unittest.main()