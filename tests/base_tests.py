import unittest
import client as c
import base_set as base
import intrigue_set as intrigue
import card as crd
import game as g
import kingdomGenerator as kg

class PlayerHandler():
	def __init__(self):
		self.log = []

	def write_json(self, **kwargs):
		if kwargs["command"] != "announce":
			self.log.append(kwargs)

class TestCard(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, PlayerHandler())
		self.player2 = c.DmClient("player2", 1, PlayerHandler())
		self.player3 = c.DmClient("player3", 2, PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [])
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for i in self.game.players:
			i.game = self.game
			i.setup()
			i.handler.log = []
		self.player1.take_turn()

	# --------------------------------------------------------
	# ------------------------- Base -------------------------
	# --------------------------------------------------------

	def test_Cellar(self):
		self.player1.hand.add(base.Cellar(self.game, self.player1))
		self.player1.hand.play("Cellar")
		self.assertTrue(self.player1.handler.log[-1]["command"] == "updateMode")
		self.assertTrue(self.player1.handler.log[-1]["mode"] == "select")
		self.assertTrue(self.player1.waiting["cb"] != None)

		selection = crd.card_list_to_titles(self.player1.hand.card_array())
		self.player1.waiting["cb"](selection)
		self.assertTrue(len(self.player1.discard_pile) == 5)

	def test_Militia(self):
		self.player1.hand.add(base.Militia(self.game, self.player1))
		self.player1.hand.play("Militia")
		self.assertTrue(self.player2.handler.log[0]["command"] == "updateMode")
		self.assertTrue(self.player2.handler.log[0]["mode"] == "select")
		self.assertTrue(self.player2.handler.log[0]["select_from"] == crd.card_list_to_titles(self.player2.hand.card_array()))
		self.assertTrue(self.player2.waiting["cb"] != None)

		selection = crd.card_list_to_titles(self.player2.hand.card_array())[:2]
		self.player2.waiting["cb"](selection)
		self.assertTrue(len(self.player2.hand) == 3)

	def test_Moat_reaction(self):
		self.player2.hand.add(base.Moat(self.game, self.player2))
		self.player1.hand.add(base.Witch(self.game, self.player1))
		self.player1.hand.play("Witch")
		self.assertTrue("Reveal" in self.player2.handler.log[0]["select_from"])
		self.player2.waiting["cb"](["Reveal"])
		# didn't gain curse
		self.assertTrue(len(self.player2.discard_pile) == 0)

	def test_Throne_Room_on_Village(self):
		throne_room_card = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(throne_room_card)
		self.player1.hand.add(base.Village(self.game, self.player1))
		throne_room_card.play()
		throne_room_card.post_select(["Village"])
		self.assertTrue(self.player1.actions == 4)

	def test_Throne_Room_on_Workshop(self):
		throne_room_card = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(throne_room_card)
		workshopCard = base.Workshop(self.game, self.player1)
		self.player1.hand.add(workshopCard)
		throne_room_card.play()
		throne_room_card.post_select(["Workshop"])
		self.assertTrue(workshopCard.done.__name__ == "second_play")

		self.player1.update_wait()
		self.player1.waiting["cb"](["Silver"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")
		self.assertTrue(workshopCard.done.__name__ == "final_done")

		self.player1.update_wait()
		self.player1.waiting["cb"](["Estate"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Estate")

	def test_Feast(self):
		feast_card = base.Feast(self.game, self.player1)
		self.player1.hand.add(feast_card)
		feast_card.play()

		self.assertTrue(self.player1.handler.log[-1]["mode"] == "selectSupply")
		self.assertTrue(self.game.trash_pile[-1] == feast_card)

	def test_Thief_2_treasures(self):
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand.add(thief_card)
		self.player2.deck.append(crd.Copper(self.game, self.player2))
		self.player2.deck.append(crd.Silver(self.game, self.player2))
		thief_card.play()
		self.assertTrue("Copper" in self.player1.handler.log[-1]['select_from'])
		self.assertTrue("Silver" in self.player1.handler.log[-1]['select_from'])
		self.player1.waiting["cb"](["Silver"])
		self.assertTrue(self.game.trash_pile[-1].title == "Silver")
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")

	def test_Thief_1_treasure(self):
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand.add(thief_card)
		self.player2.deck.append(crd.Estate(self.game, self.player2))
		self.player2.deck.append(crd.Gold(self.game, self.player2))
		thief_card.play()
		self.assertTrue(self.game.trash_pile[-1].title == "Gold")
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Gold")

	def test_Thief_3_players(self):
		thief_card = base.Thief(self.game, self.player1)
		self.player1.hand.add(thief_card)
		self.player2.deck.append(crd.Estate(self.game, self.player2))
		self.player2.deck.append(crd.Gold(self.game, self.player2))
		self.player3.deck.append(crd.Copper(self.game, self.player2))
		self.player3.deck.append(crd.Estate(self.game, self.player2))
		thief_card.play()
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Gold")
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Copper")
		thief_card.play()

	def test_Gardens(self):
		gardens = base.Gardens(self.game, self.player1)
		self.player1.hand.add(gardens)
		self.assertTrue(gardens.get_vp() == 1)
		for i in range(0, 9):
			self.player1.deck.append(base.Gardens(self.game, self.player1))
		# decksize = 20
		self.assertTrue(self.player1.total_vp() == 23)
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.assertTrue(self.player1.total_vp() == 23)

	def test_Chancellor(self):
		self.player1.discard_pile.append(crd.Copper(self.game, self.player1))
		chancellor = base.Chancellor(self.game, self.player1)
		self.player1.hand.add(chancellor)
		chancellor.play()
		self.assertTrue(self.player1.handler.log[-1]["command"] == "updateMode")
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

		self.player1.hand.add(adventurer)
		adventurer.play()
		self.assertTrue(self.player1.hand.get_count("Gold") == 2)
		self.assertTrue(len(self.player1.deck) == 0)
		self.assertTrue(len(self.player1.discard_pile) == 3)

	def test_Library(self):
		library = base.Library(self.game, self.player1)
		village = base.Village(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.deck = [copper, village, copper]
		self.player1.hand.add(library)
		library.play()
		self.assertTrue(len(self.player1.hand) == 6)
		self.assertTrue(self.player1.handler.log[-1]["command"] == "updateMode")
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(len(self.player1.hand) == 7)
		self.assertTrue(self.player1.discard_pile[-1] == village)


if __name__ == '__main__':
	unittest.main()