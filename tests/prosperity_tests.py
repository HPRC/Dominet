import unittest
import client as c
import base_set as base
import intrigue_set as intrigue
import prosperity_set as prosperity
import card as crd
import game as g
import kingdomGenerator as kg

import sys
import os
# add this file's path to the sys for importing base_tests
sys.path.append(os.path.dirname(__file__))
import base_tests as bt
import intrigue_tests as it


class TestProsperity(unittest.TestCase):
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
		self.game.players = [self.player1, self.player2, self.player3]
		self.player1.take_turn()

	# --------------------------------------------------------
	# ---------------------- Prosperity ----------------------
	# --------------------------------------------------------

	def test_Monument(self):
		monument = prosperity.Monument(self.game, self.player1)
		monument.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.vp == 1)

		self.assertTrue(self.player1.total_vp() == 4)

	def test_Counting_House(self):
		counting_house = prosperity.Counting_House(self.game, self.player1)
		copper1 = crd.Copper(self.game, self.player1)
		copper2 = crd.Copper(self.game, self.player1)
		copper3 = crd.Copper(self.game, self.player1)

		num_coppers = self.player1.hand.get_count('Copper')

		self.player1.discard_pile.append(copper1)
		self.player1.discard_pile.append(copper2)
		self.player1.discard_pile.append(copper3)

		counting_house.play()

		self.assertTrue(self.player1.hand.get_count('Copper') == num_coppers + 3)
		self.assertTrue(len(self.player1.discard_pile) == 0)

	def test_Workers_Village(self):
		workers_village = prosperity.Workers_Village(self.game, self.player1)

		workers_village.play()

		self.assertTrue(len(self.player1.hand.card_array()) == 6)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.actions == 2)

	def test_Expand(self):
		expand = prosperity.Expand(self.game, self.player1)

		expand.play()

		self.player1.waiting["cb"](["Copper"])

		self.player1.waiting["cb"](["Silver"])

		self.assertTrue(self.player1.discard_pile[0].title == "Silver")

	def test_Mint(self):
		mint = prosperity.Mint(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)

		mint.play()

		self.assertTrue(self.player1.discard_pile[0].title == "Copper")

		self.player1.hand.add(silver)
		self.player1.hand.add(silver)
		mint.play()

		self.player1.waiting["cb"](["Silver"])
		self.assertTrue(self.player1.discard_pile[1].title == "Silver")

		self.player1.spend_all_money()
		self.player1.buy_card('Mint')
		self.assertTrue(len(self.game.trash_pile) >= 5)

	def test_Mountebank(self):
		mountebank = prosperity.Mountebank(self.game, self.player1)
		curse = crd.Curse(self.game, self.player2)

		self.player2.hand.add(curse)

		mountebank.play()

		self.assertTrue(self.player1.balance == 2)
		self.player2.waiting["cb"](["Yes"])

		self.assertTrue(self.player2.discard_pile[0].title == "Curse")
		self.assertTrue(self.player3.discard_pile[0].title == "Copper")
		self.assertTrue(self.player3.discard_pile[1].title == "Curse")

	def test_Bishop(self):
		bishop = prosperity.Bishop(self.game, self.player1)
		steward = intrigue.Steward(self.game, self.player1)
		self.player1.hand.add(steward)

		bishop.play()
		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(self.player1.vp == 1)

		self.player1.waiting["cb"](["Steward"])

		self.assertTrue(self.player1.vp == 2)

		self.player2.waiting["cb"](["None"])
		self.player3.waiting["cb"](["Copper"])

		self.assertTrue(len(self.player3.hand.card_array()) == 4)
		self.assertTrue(len(self.player2.hand.card_array()) == 5)

	def test_Forge(self):
		forge = prosperity.Forge(self.game, self.player1)
		steward = intrigue.Steward(self.game, self.player1)
		minion = intrigue.Minion(self.game, self.player1)
		torturer = intrigue.Torturer(self.game, self.player1)
		secret_chamber = intrigue.Secret_Chamber(self.game, self.player1)
		gold = crd.Gold(self.game, self.player1)

		self.player1.hand.add(steward)
		self.player1.hand.add(minion)
		self.player1.hand.add(torturer)
		self.player1.hand.add(secret_chamber)
		self.player1.hand.add(gold)

		forge.play()
		# trash prices total to 8
		self.player1.waiting["cb"](["Steward", "Copper", "Copper", "Minion"])
		self.assertTrue(len(self.game.trash_pile) == 4)
		self.player1.waiting["cb"](["Province"])
		self.assertTrue(self.player1.discard_pile[0].title == "Province")

		forge.play()
		# trash prices total to 13 -- nothing to gain
		self.player1.waiting["cb"](["Torturer", "Secret Chamber", "Gold"])
		self.assertTrue(self.player1.waiting["cb"] is None)

	def test_City(self):
		city = prosperity.City(self.game, self.player1)

		cards_in_hand = len(self.player1.hand.card_array())

		city.play()
		self.assertTrue(self.player1.balance == 0)
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(len(self.player1.hand.card_array()) == cards_in_hand + 1)
		self.assertTrue(self.player1.buys == 1)
		self.assertTrue(self.player1.balance == 0)

		self.game.empty_piles = 1

		city.play()
		self.assertTrue(len(self.player1.hand.card_array()) == cards_in_hand + 3)
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(self.player1.buys == 1)
		self.assertTrue(self.player1.balance == 0)

		self.game.empty_piles = 2

		city.play()
		self.assertTrue(len(self.player1.hand.card_array()) == cards_in_hand + 5)
		self.assertTrue(self.player1.actions == 4)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.balance == 1)

	def test_Loan(self):
		loan = prosperity.Loan(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)

		self.player1.deck.append(estate)
		self.player1.deck.append(estate)
		self.player1.deck.append(estate)

		loan.play()

		self.player1.balance = 1
		self.assertTrue("Treasure" in self.player1.deck[0].type)
		self.assertTrue(len(self.player1.discard_pile) >= 3)

		self.player1.waiting["cb"](["Trash"])

		self.assertTrue(len(self.game.trash_pile) == 1)

	def test_Venture(self):
		venture = prosperity.Venture(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		loan = prosperity.Loan(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)

		self.player1.deck.append(loan)
		self.player1.deck.append(estate)
		self.player1.deck.append(estate)
		self.player1.deck.append(silver)
		self.player1.deck.append(estate)

		venture.play()

		self.assertTrue(len(self.player1.discard_pile) == 1)
		self.assertTrue(self.player1.balance == 3)

		venture.play()

		# self.assertTrue(len(self.player1.discard_pile) == 4)
		self.assertTrue(self.player1.balance == 5)

		self.player1.waiting["cb"]("Trash")
		self.assertTrue(self.game.trash_pile[0].title == "Copper")

	def test_Vault(self):
		vault = prosperity.Vault(self.game, self.player1)

		vault.play()

		self.player1.waiting["cb"](["Estate", "Estate"])
		self.assertTrue(self.player1.balance == 2)

		self.player2.waiting["cb"](["Yes"])
		cards_in_hand = len(self.player2.hand.card_array())
		self.player2.waiting["cb"](["Copper", "Copper"])
		self.assertTrue(len(self.player2.hand.card_array()) == cards_in_hand - 1)

		self.player3.waiting["cb"](["No"])

	def test_Bank(self):
		bank = prosperity.Bank(self.game, self.player1)
		self.player1.hand.add(bank)

		bank.play()
		self.assertTrue(self.player1.balance == 1)

		self.player1.hand.add(bank)
		self.player1.spend_all_money()
		coppers = self.player1.balance - 1
		bank.play()
		self.assertTrue(self.player1.balance == (3 + coppers + coppers))

	def test_Hoard(self):
		hoard = prosperity.Hoard(self.game, self.player1)
		woodcutter = base.Woodcutter(self.game, self.player1)

		woodcutter.play()
		self.player1.hand.add(hoard)
		self.player1.hand.add(hoard)
		hoard.play()
		hoard.play()

		self.assertTrue(self.player1.balance == 6)

		self.player1.buy_card('Estate')
		self.player1.buy_card('Estate')

		golds = self.player1.get_card_count_in_list('Gold', self.player1.discard_pile)

		self.assertTrue(golds == 4)

	def test_Talisman(self):
		talisman = prosperity.Talisman(self.game, self.player1)
		self.player1.hand.add(talisman)
		self.player1.hand.add(talisman)

		talisman.play()
		talisman.play()
		self.assertTrue(self.player1.balance == 2)

		self.player1.balance = 8
		self.player1.buys = 2

		self.player1.buy_card('Gardens')
		self.player1.buy_card('Mining Village')

		gardens = self.player1.get_card_count_in_list('Gardens', self.player1.discard_pile)
		mining_villages = self.player1.get_card_count_in_list('Mining Village', self.player1.discard_pile)

		self.assertTrue(gardens == 1)
		self.assertTrue(mining_villages == 3)

	def test_Goons(self):
		goons = prosperity.Goons(self.game, self.player1)
		self.player1.hand.add(goons)
		self.player1.hand.add(goons)

		self.player1.actions = 2

		goons.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.buys == 2)

		self.player2.waiting["cb"](["Copper", "Copper"])
		self.player3.waiting["cb"](["Copper", "Copper"])

		goons.play()

		self.player1.buy_card("Copper")
		self.assertTrue(self.player1.vp == 2)
		self.player1.buy_card("Copper")
		self.player1.buy_card("Copper")
		self.assertTrue(self.player1.vp == 6)

	def test_Rabble(self):
		rabble = prosperity.Rabble(self.game, self.player1)
		copper = crd.Copper(self.game, self.player2)
		estate = crd.Estate(self.game, self.player2)

		self.player2.deck.append(estate)
		self.player2.deck.append(copper)
		self.player2.deck.append(estate)

		duchy = crd.Duchy(self.game, self.player3)
		gardens = base.Gardens(self.game, self.player3)
		great_hall = intrigue.Great_Hall(self.game, self.player3)

		self.player3.deck.append(duchy)
		self.player3.deck.append(gardens)
		self.player3.deck.append(great_hall)

		rabble.play()

		topdeck1 = self.player2.topdeck()
		topdeck2 = self.player2.topdeck()
		self.assertTrue(topdeck1.title == "Estate")
		self.assertTrue(topdeck2.title == "Estate")

		self.player3.waiting["cb"](["Gardens", "Duchy"])

		topdeck1 = self.player3.topdeck()
		topdeck2 = self.player3.topdeck()

		self.assertTrue(topdeck1.title == "Duchy")
		self.assertTrue(topdeck2.title == "Gardens")






if __name__ == '__main__':
	unittest.main()