import unittest
import client as c
import base_set as base
import intrigue_set as intrigue
import card as crd
import game as g
import kingdomGenerator as kg

import sys
import os
#add this file's path to the sys for importing base_tests
sys.path.append(os.path.dirname(__file__))
import base_tests as bt

class TestIntrigue(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, bt.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, bt.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, bt.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [])
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for i in self.game.players:
			i.game = self.game
			i.setup()
			i.handler.log = []
		self.player1.take_turn()


	# --------------------------------------------------------
	# ----------------------- Intrigue -----------------------
	# --------------------------------------------------------

	def test_Pawn(self):
		pawn = intrigue.Pawn(self.game, self.player1)
		self.player1.hand.add(pawn)
		pawn.play()
		self.player1.waiting["cb"](["+$1", "+1 Action"])
		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(self.player1.actions == 1)

	def test_Great_Hall(self):
		great_hall = intrigue.Great_Hall(self.game, self.player1)
		player1_vp = self.player1.total_vp()
		self.player1.hand.add(great_hall)
		great_hall.play()
		self.assertTrue((self.player1.actions == 1))
		self.assertTrue((self.player1.total_vp()) == player1_vp + 1)

	def test_Steward(self):
		steward = intrigue.Steward(self.game, self.player1)
		steward2 = intrigue.Steward(self.game, self.player1)
		steward3 = intrigue.Steward(self.game, self.player1)

		copper = crd.Copper(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		self.player1.hand.data = {}
		self.player1.hand.add(steward)
		self.player1.hand.add(steward2)
		self.player1.hand.add(steward3)
		self.player1.hand.add(copper)
		self.player1.hand.add(copper)
		self.player1.hand.add(copper)
		self.player1.hand.add(estate)
		self.player1.hand.add(estate)

		self.player1.actions = 5
		# +$2
		steward.play()
		self.player1.waiting["cb"](["+$2"])
		self.assertTrue(self.player1.balance == 2)

		# Trash 2 with more than 2 in hand
		steward2.play()
		trash_size = len(self.game.trash_pile)
		self.player1.waiting["cb"](["Trash 2 cards from hand"])
		self.player1.waiting["cb"](["Estate", "Estate"])
		self.assertTrue(len(self.game.trash_pile) == trash_size + 2)

		# Trash 2 with homogeneous hand
		steward3.play()
		self.player1.waiting["cb"](["Trash 2 cards from hand"])
		self.assertTrue(self.player1.hand.get_count("Copper") == 1)

		self.player1.hand.add(steward)

		# Trash 2 with 1 in hand
		self.player1.hand.data["Steward"] = [intrigue.Steward(self.game, self.player1)]
		steward.play()
		self.player1.waiting["cb"](["Trash 2 cards from hand"])
		self.assertTrue(len(self.player1.hand) == 0)

	def test_Baron(self):
		baron = intrigue.Baron(self.game, self.player1)
		self.player1.hand.data = {}
		self.player1.hand.add(baron)
		self.player1.hand.add(baron)
		self.player1.hand.add(baron)
		estate = crd.Estate(self.game, self.player1)
		# sadly add an estate to hand since no guarantees -- actually overwrites hand
		self.player1.hand.add(estate)
		self.player1.actions = 3


		# decline Estate discard, gain Estate to discard pile.
		baron.play()
		self.player1.waiting["cb"](["No"])
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(len(self.player1.discard_pile) == 1)

		# accept Estate discard, do not gain Estate to discard pile, gain $4
		baron.play()
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.buys == 3)
		self.assertTrue(self.player1.balance == 4)
		self.assertFalse("Estate" in self.player1.hand)

		# Not given option because no Estates in hand.
		baron.play()
		self.assertTrue(self.player1.buys == 4)

	def test_Shanty_Town(self):
		shanty_town = intrigue.Shanty_Town(self.game, self.player1)
		self.player1.hand.add(shanty_town)
		self.player1.hand.add(shanty_town)

		# First Play: has an action, should not draw cards.
		cards_in_hand = len(self.player1.hand)
		shanty_town.play()
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(len(self.player1.hand) == cards_in_hand - 1)

		# Second Play: has no other action cards in hand, should draw cards.
		shanty_town.play()
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(len(self.player1.hand) == cards_in_hand)

	def test_Conspirator(self):
		conspirator = intrigue.Conspirator(self.game, self.player1)
		self.player1.hand.add(conspirator)
		self.player1.hand.add(conspirator)

		village = base.Village(self.game, self.player1)
		self.player1.hand.add(village)

		village.play()
		conspirator.play()
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.balance == 2)

		cards_in_hand = len(self.player1.hand)
		conspirator.play()
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(len(self.player1.hand) == cards_in_hand)

	def test_Courtyard(self):
		courtyard = intrigue.Courtyard(self.game, self.player1)
		self.player1.hand.add(courtyard)

		cards_in_hand = len(self.player1.hand)

		courtyard.play()
		self.player1.waiting["cb"](["Copper"])

		self.assertTrue(len(self.player1.hand) == cards_in_hand + 1)
		topdeck = self.player1.topdeck()
		self.assertTrue(topdeck.title == "Copper")

	def test_Nobles(self):
		nobles = intrigue.Nobles(self.game, self.player1)
		self.player1.hand.add(nobles)
		self.player1.hand.add(nobles)

		nobles.play()
		self.player1.waiting["cb"](["+2 Actions"])
		self.assertTrue(self.player1.actions == 2)

		cards_in_hand = len(self.player1.hand)

		nobles.play()
		self.player1.waiting["cb"](["+3 Cards"])
		self.assertTrue(len(self.player1.hand) == cards_in_hand + 2)

	def test_Swindler(self):
		swindler = intrigue.Swindler(self.game, self.player1)
		self.player2.deck.append(crd.Copper(self, self.player2))
		self.player1.hand.add(swindler)

		swindler.play()

		self.player1.waiting["cb"]("Curse")

	def test_Duke(self):
		duke = intrigue.Duke(self.game, self.player1)
		self.player1.hand.add(duke)

		duchy = crd.Duchy(self.game, self.player1)
		self.player1.hand.add(duchy)
		self.player1.deck.append(duchy)
		self.player1.discard_pile.append(duchy)

		self.assertTrue(duke.get_vp() == 3)

	def test_Wishing_Well(self):
		wishing_well = intrigue.Wishing_Well(self.game, self.player1)
		self.player1.hand.add(wishing_well)
		self.player1.hand.add(wishing_well)
		province = crd.Province(self.game, self.player1)
		self.player1.deck.append(province)
		self.player1.deck.append(province)

		wishing_well.play()
		self.player1.waiting["cb"]("Province")
		self.assertTrue(self.player1.hand.get_count('Province') == 1)

		wishing_well.play()
		self.player1.waiting["cb"]("Copper")
		self.assertTrue(self.player1.hand.get_count('Province') == 1)

	def test_Upgrade(self):
		upgrade = intrigue.Upgrade(self.game, self.player1)
		self.player1.hand.add(upgrade)
		self.player1.hand.add(upgrade)

		upgrade.play()
		self.player1.waiting["cb"](["Copper"])

		upgrade.play()
		self.player1.waiting["cb"](["Estate"])

	def test_Torturer(self):
		torturer = intrigue.Torturer(self.game, self.player1)
		self.player1.hand.add(torturer)
		self.player1.hand.add(torturer)
		self.player1.actions = 2

		torturer.play()
		# choosing to discard 2
		self.player2.waiting["cb"](["Discard 2 cards"])
		self.player2.waiting["cb"](['Copper', 'Copper'])

		torturer.play()
		self.player2.waiting["cb"](["Gain a Curse"])
		self.assertTrue(self.player2.hand.get_count('Curse') == 1)

		self.player1.actions = 1
		copper = crd.Copper(self.game, self.player1)
		self.player2.hand.add(copper)
		self.player2.hand.add(copper)
		self.player2.hand.add(copper)

		torturer.play()
		self.player2.waiting["cb"](["Discard 2 cards"])

	def test_Trading_Post(self):
		trading_post = intrigue.Trading_Post(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.data = {}
		self.player1.hand.add(copper)
		self.player1.hand.add(trading_post)
		self.player1.actions = 3

		trading_post.play()
		self.assertTrue(len(self.player1.hand.data) == 0)

		self.player1.hand.data = {}
		self.player1.hand.add(copper)
		self.player1.hand.add(copper)
		self.player1.hand.add(trading_post)

		trading_post.play()
		self.assertTrue(self.player1.hand.get_count("Silver") == 1)

		self.player1.hand.add(trading_post)
		self.player1.hand.add(trading_post)
		self.player1.hand.add(trading_post)
		trading_post.play()
		self.player1.waiting["cb"](["Trading Post", "Trading Post"])
		self.assertTrue(self.player1.hand.get_count("Silver") == 2)

	def test_Ironworks(self):
		ironworks = intrigue.Ironworks(self.game, self.player1)
		self.player1.hand.add(ironworks)
		self.player1.hand.add(ironworks)
		self.player1.hand.add(ironworks)
		self.player1.hand.add(ironworks)
		self.player1.actions = 2

		ironworks.play()
		self.player1.waiting["cb"]("Steward")
		self.assertTrue(self.player1.actions == 2)

		ironworks.play()
		self.player1.waiting["cb"]("Silver")
		self.assertTrue(self.player1.balance == 1)

		ironworks.play()
		cards_in_hand = len(self.player1.hand.card_array())
		self.player1.waiting["cb"]("Great Hall")
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.hand == cards_in_hand + 1)

	def test_Secret_Chamber(self):
		secret_chamber = intrigue.Secret_Chamber(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		self.player1.hand.data = {
			"Estate": [estate, 4],
			"Secret Chamber": [secret_chamber, 1]
		}

		secret_chamber.play()
		self.player1.waiting["cb"](["Estate", "Estate", "Estate", "Estate"])
		self.assertTrue(self.player1.balance == 4)

		self.player1.hand.data = {
			"Estate": [estate, 4],
			"Secret Chamber": [secret_chamber, 1]
		}
		self.player2.hand.add(base.Militia(self.game, self.player2))
		self.player2.hand.play("Militia")
		self.player1.waiting["cb"](["Reveal"])
		self.player1.waiting["cb"](["Estate", "Estate"])
		self.player1.waiting["cb"](["Estate", "Estate"])
		self.assertTrue(len(self.player1.hand.card_array()) == 3)

		estates = self.player1.hand.get_count("Estate")
		self.player1.draw(2)
		self.assertTrue(self.player1.hand.get_count("Estate") == estates + 2)

	def test_Tribute(self):
		tribute = intrigue.Tribute(self.game, self.player1)
		self.player1.hand.add(tribute, 2)
		estate = crd.Estate(self.game, self.player2)
		copper = crd.Copper(self.game, self.player2)
		great_hall = intrigue.Great_Hall(self.game, self.player2)
		swindler = intrigue.Swindler(self.game, self.player2)

		self.player2.deck.append(estate)
		self.player2.deck.append(copper)
		self.player2.deck.append(great_hall)
		self.player2.deck.append(swindler)

		cards_in_hand = len(self.player1.hand.card_array())
		tribute.play()
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(len(self.player1.hand.card_array()) == cards_in_hand)
		self.assertTrue(len(self.player2.discard_pile) == 2)

		tribute.play()
		self.assertTrue(self.player1.balance == 1)

	def test_Mining_Village(self):
		mining_village = intrigue.Mining_Village(self.game, self.player1)
		self.player1.hand.add(mining_village, 2)
		mining_village.play()

		self.assertTrue(self.player1.actions == 2)

		self.player1.waiting["cb"](["No"])
		self.assertTrue(self.player1.balance == 0)

		mining_village.play()
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(len(self.game.trash_pile) == 1)


	def test_Mining_Village(self):
		mining_village = intrigue.Mining_Village(self.game, self.player1)
		mining_village2 = intrigue.Mining_Village(self.game, self.player1)
		self.player1.hand.add(mining_village)
		self.player1.hand.add(mining_village2)

		mining_village.play()
		self.player1.waiting["cb"](["No"])
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(mining_village not in self.game.trash_pile)

		#note discard takes in a string as a parameter so the trashed mining village
		# could be mining_village or mining_village2 it is not guaranteed to be the same
		mining_village2.play()
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(self.game.trash_pile[-1].title == "Mining Village")
		self.assertTrue(self.player1.balance == 2)

	def test_Mining_Village_Throne_Room(self):
		mining_village = intrigue.Mining_Village(self.game, self.player1)
		mining_village2 = intrigue.Mining_Village(self.game, self.player1)
		throne_room = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(mining_village)
		self.player1.hand.add(mining_village2)
		self.player1.hand.add(throne_room)

		throne_room.play()
		self.player1.waiting["cb"](["Mining Village"])
		self.assertTrue(self.player1.actions, 2)
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.balance == 2)
		self.player1.waiting["cb"]("Yes")
		self.assertTrue(self.player1.balance == 2)

if __name__ == '__main__':
	unittest.main()