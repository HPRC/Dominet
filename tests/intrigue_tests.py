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
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [])
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

	def test_Conspirator_Throne_Room(self):
		conspirator = intrigue.Conspirator(self.game, self.player1)
		throne_room = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(conspirator)
		self.player1.hand.add(throne_room)
		throne_room.play()
		handsize = len(self.player1.hand)
		self.player1.waiting["cb"](["Conspirator"])
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.balance == 4)
		#discard conspirator, draw 1 card should have same handsize
		self.assertTrue(handsize == len(self.player1.hand))

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

		self.player1.waiting["cb"](["Curse"])

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
		self.player1.deck.append(crd.Silver(self.game, self.player1))
		self.player1.deck.append(province)

		wishing_well.play()

		self.player1.waiting["cb"](["Province"])
		self.assertTrue(self.player1.hand.get_count('Province') == 1)

		wishing_well.play()
		self.player1.waiting["cb"](["Copper"])
		self.assertTrue(self.player1.hand.get_count('Province') == 1)

	def test_Upgrade(self):
		upgrade = intrigue.Upgrade(self.game, self.player1)
		self.player1.hand.add(upgrade)
		self.player1.hand.add(upgrade)
		self.player1.hand.add(crd.Copper(self.game, self.player1))
		self.player1.hand.add(crd.Estate(self.game, self.player1))

		upgrade.play()
		self.player1.waiting["cb"](["Copper"])

		upgrade.play()
		self.player1.waiting["cb"](["Estate"])
		self.player1.waiting["cb"](["Silver"])
		self.assertTrue("Silver" == self.player1.discard_pile[-1].title)

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
		self.player1.waiting["cb"](["Steward"])
		self.assertTrue(self.player1.actions, 2)

		ironworks.play()
		self.player1.waiting["cb"](["Silver"])
		self.assertTrue(self.player1.balance, 1)

		ironworks.play()
		cards_in_hand = len(self.player1.hand.card_array())
		self.player1.waiting["cb"](["Great Hall"])
		self.assertTrue(self.player1.actions, 1)
		self.assertTrue(self.player1.hand, cards_in_hand + 1)

	def test_Secret_Chamber(self):
		secret_chamber = intrigue.Secret_Chamber(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		self.player1.hand.data = {
			"Estate": [estate for i in range(0,4)],
			"Secret Chamber": [secret_chamber]
		}

		secret_chamber.play()
		self.player1.waiting["cb"](["Estate", "Estate", "Estate", "Estate"])
		self.assertTrue(self.player1.balance == 4)

		self.player1.hand.data = {
			"Estate": [estate for i in range(0,4)],
			"Secret Chamber": [secret_chamber]
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
		self.player1.hand.add(tribute)
		self.player1.hand.add(tribute)
		copper = crd.Copper(self.game, self.player2)
		great_hall = intrigue.Great_Hall(self.game, self.player2)
		swindler = intrigue.Swindler(self.game, self.player2)

		self.player2.deck.append(copper)
		self.player2.deck.append(copper)
		self.player2.deck.append(great_hall)
		self.player2.deck.append(swindler)

		cards_in_hand = len(self.player1.hand.card_array())
		tribute.play()
		self.assertTrue(self.player1.actions == 4)
		self.assertTrue(len(self.player2.discard_pile) == 2)

		tribute.play()
		self.assertTrue(self.player1.balance == 2)

	def test_Mining_Village(self):
		mining_village = intrigue.Mining_Village(self.game, self.player1)
		mining_village2 = intrigue.Mining_Village(self.game, self.player1)
		self.player1.hand.add(mining_village)
		self.player1.hand.add(mining_village2)

		mining_village.play()
		self.player1.waiting["cb"](["No"])
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(mining_village not in self.game.trash_pile)

		# note discard takes in a string as a parameter so the trashed mining village
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
		self.player1.waiting["cb"](["Yes"])
		self.assertTrue(self.player1.balance == 2)

	def test_Bridge(self):
		bridge = intrigue.Bridge(self.game, self.player1)
		self.player1.hand.add(bridge)
		bridge.play()
		self.assertTrue(self.player1.balance == 1)
		self.player1.buy_card("Estate")
		self.assertTrue(self.player1.balance == 0)
		self.assertTrue(self.player1.buys == 1)

	def test_Coppersmith(self):
		coppersmith = intrigue.Coppersmith(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.add(coppersmith)
		self.player1.hand.add(copper)

		coppersmith.play()
		copper.play()
		self.assertTrue(self.player1.balance == 2)
		#copper should be back to $1 after turn
		self.player1.end_turn()
		self.assertTrue(copper.value == 1)

	def test_Coppersmith_Throne_Room(self):
		coppersmith = intrigue.Coppersmith(self.game, self.player1)
		throneroom = base.Throne_Room(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.add(coppersmith)
		self.player1.hand.add(throneroom)
		self.player1.hand.add(copper)

		throneroom.play()
		self.player1.waiting["cb"](["Coppersmith"])
		copper.play()
		self.assertTrue(self.player1.balance == 3)
		#we played throne room, coppersmith, coppersmith, copper
		self.assertTrue(len(self.player1.played) == 4)
		self.player1.end_turn()
		self.assertTrue(copper.value == 1)
		#make sure we only have 1 coppersmith in our deck
		coppersmiths = [x for x in self.player1.all_cards() if x.title == "Coppersmith"]
		self.assertTrue(len(coppersmiths) == 1)

	def test_Scout(self):
		scout = intrigue.Scout(self.game, self.player1)
		scout2 = intrigue.Scout(self.game, self.player1)
		province = crd.Province(self.game, self.player1)
		greathall = intrigue.Great_Hall(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)
		self.player1.hand.add(scout)
		self.player1.deck.append(province)
		self.player1.deck.append(greathall)
		self.player1.deck.append(scout2)
		self.player1.deck.append(silver)
		decklength = len(self.player1.deck)
		scout.play()

		self.assertTrue(greathall.title in self.player1.hand)
		self.assertTrue(province.title in self.player1.hand)
		self.assertFalse(silver.title in self.player1.hand)
		self.assertFalse(scout2.title in self.player1.hand)

		self.player1.waiting["cb"](["Silver", "Scout"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")
		self.assertTrue(self.player1.deck[-2].title == "Scout")
		#decksize should be 2 less since we took province and great hall out
		self.assertTrue(len(self.player1.deck) == decklength - 2)

	def test_Scout_autoselect(self):
		scout = intrigue.Scout(self.game, self.player1)
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.player1.deck.append(crd.Estate(self.game, self.player1))
		self.player1.deck.append(crd.Estate(self.game, self.player1))
		self.player1.hand.add(scout)

		scout.play()
		self.assertTrue(self.player1.deck[-1].title == "Copper")
		self.assertTrue(self.player1.deck[-2].title == "Copper")


	def test_Minion(self):
		minion = intrigue.Minion(self.game, self.player1)
		self.player1.hand.add(minion)
		moat = base.Moat(self.game, self.player3)
		self.player3.hand.add(moat)
		#top 4 cards of player2's deck will be drawn
		top4 = self.player2.deck[-4:]
		discard_size = len(self.player2.discard_pile)
		minion.play()
		self.player1.exec_commands({"command": "post_selection", "selection": ["discard hand and draw 4 cards"]})
		self.player3.exec_commands({"command": "post_selection", "selection": ["Reveal"]})
		self.assertTrue(len(self.player1.hand) == 4)
		self.assertTrue(len(self.player2.hand) == 4)
		for x in top4:
			self.assertTrue(x in self.player2.hand.card_array())
		self.assertTrue(discard_size + 5 == len(self.player2.discard_pile))
		self.assertTrue(len(self.player3.hand) > 4)

	def test_Minion_Throne_Room(self):
		minion = intrigue.Minion(self.game, self.player1)
		throneroom = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(minion)
		self.player1.hand.add(throneroom)
		throneroom.play()
		self.player1.exec_commands({"command": "post_selection", "selection": ["Minion"]})
		self.player1.exec_commands({"command": "post_selection", "selection": ["+$2"]})
		self.player1.exec_commands({"command": "post_selection", "selection": ["discard hand and draw 4 cards"]})
		self.assertTrue(len(self.player1.hand) == 4)
		self.assertTrue(self.player1.balance == 2)

	def test_Masquerade(self):
		masquerade = intrigue.Masquerade(self.game, self.player1)
		curse = crd.Curse(self.game, self.player1)
		baron = intrigue.Baron(self.game, self.player2)
		tribute = intrigue.Tribute(self.game, self.player3)

		self.player1.hand.add(masquerade)
		self.player1.hand.add(curse)
		self.player2.hand.add(baron)
		self.player3.hand.add(tribute)

		masquerade.play()
		self.assertTrue(self.player1.hand.get_count("Curse") == 1)
		self.player1.waiting["cb"](["Curse"])
		self.assertTrue(self.player1.hand.get_count("Curse") == 0)
		self.assertTrue(self.player2.hand.get_count("Curse") == 1)

		self.assertTrue(self.player2.hand.get_count("Baron") == 1)
		self.player2.waiting["cb"](["Baron"])
		self.assertTrue(self.player2.hand.get_count("Baron") == 0)
		self.assertTrue(self.player3.hand.get_count("Baron") == 1)

		self.assertTrue(self.player3.hand.get_count("Tribute") == 1)
		self.player3.waiting["cb"](["Tribute"])
		self.assertTrue(self.player3.hand.get_count("Tribute") == 0)
		self.assertTrue(self.player1.hand.get_count("Tribute") == 1)

		self.player1.waiting["cb"](["Tribute"])
		self.assertTrue(self.player1.hand.get_count("Tribute") == 0)

	def test_Masquerade_waits(self):
		masquerade = intrigue.Masquerade(self.game, self.player1)
		curse = crd.Curse(self.game, self.player1)
		estate = crd.Estate(self.game, self.player2)
		estate3 = crd.Estate(self.game, self.player3)
		self.player1.hand.add(masquerade)
		self.player1.hand.add(curse)
		self.player2.hand.add(estate)
		self.player3.hand.add(estate3)

		masquerade.play()
		self.player1.exec_commands({"command": "post_selection", "selection": ["Curse"]})
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.player2.exec_commands({"command": "post_selection", "selection": ["Estate"]})
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.player3.exec_commands({"command": "post_selection", "selection": ["Estate"]})
		self.assertTrue(self.player1.last_mode["mode"] == "select")

	def test_Saboteur(self):
		saboteur = intrigue.Saboteur(self.game, self.player1)
		steward = intrigue.Steward(self.game, self.player2)
		copper = crd.Copper(self.game, self.player2)

		self.player2.deck.append(steward)
		self.player2.deck.append(copper)
		player3_decksize = len(self.player3.deck)

		saboteur.play()

		self.player2.waiting["cb"](["Curse"])

		self.assertTrue(self.player2.discard_pile.pop().title == "Curse")
		self.assertTrue(self.player2.discard_pile.pop().title == "Copper")
		self.assertTrue(len(self.player3.deck) == 0)
		self.assertTrue(player3_decksize == len(self.player3.discard_pile))

if __name__ == '__main__':
	unittest.main()