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
# add this file's path to the sys for importing test_utils
sys.path.append(os.path.dirname(__file__))
import test_utils as tu


class TestProsperity(unittest.TestCase):
	def setUp(self):
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [])
		#todo use game initialization setup
		self.game.supply = self.game.init_supply(kg.all_cards(self.game))
		for x in self.game.supply.unique_cards():
			x.on_supply_init()
		for x in self.game.supply.unique_cards():
			self.game.price_modifier[x.title] = 0
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
		tu.print_test_header("test Monument")
		monument = prosperity.Monument(self.game, self.player1)
		monument.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.vp == 1)

		self.assertTrue(self.player1.total_vp() == 4)

	def test_Counting_House(self):
		tu.print_test_header("test Counting House")
		counting_house = prosperity.Counting_House(self.game, self.player1)
		copper1 = crd.Copper(self.game, self.player1)
		copper2 = crd.Copper(self.game, self.player1)
		copper3 = crd.Copper(self.game, self.player1)

		num_coppers = self.player1.hand.get_count('Copper')
		self.player1.discard_pile = []
		self.player1.discard_pile.append(copper1)
		self.player1.discard_pile.append(copper2)
		self.player1.discard_pile.append(copper3)
		all_copper = len([x for x in self.player1.all_cards() if x.title == "Copper"])
		
		counting_house.play()
		tu.send_input(self.player1, "post_selection", [2])
		self.assertTrue(self.player1.hand.get_count('Copper') == num_coppers + 2)
		self.assertTrue(len(self.player1.discard_pile) == 1)
		self.assertTrue(len([x for x in self.player1.all_cards() if x.title == "Copper"]) == all_copper)

	def test_Workers_Village(self):
		tu.print_test_header("test Worker's Village")
		workers_village = prosperity.Workers_Village(self.game, self.player1)

		workers_village.play()

		self.assertTrue(len(self.player1.hand.card_array()) == 6)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.actions == 2)

	def test_Expand(self):
		tu.print_test_header("testing expand")
		expand = prosperity.Expand(self.game, self.player1)

		expand.play()
		tu.send_input(self.player1, "post_selection", ["Copper"])
		tu.send_input(self.player1, "post_selection", ["Silver"])

		self.assertTrue(self.player1.discard_pile[0].title == "Silver")

	def test_Watchtower_play(self):
		tu.print_test_header("testing Watchtower play action")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		watchtower2 = prosperity.Watchtower(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		tu.set_player_hand(self.player1, [watchtower, estate, watchtower2])
		self.player1.actions = 2
		watchtower.play()
		#3 cards in hand
		self.assertTrue(len(self.player1.hand) == 6)
		#7 cards in hand
		tu.set_player_hand(self.player1, [estate, estate, watchtower2, estate, estate, estate, estate])
		watchtower2.play()
		self.assertTrue(len(self.player1.hand) == 6)

	def test_Watchtower_react(self):
		tu.print_test_header("testing Watchtower reaction")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		tu.set_player_hand(self.player1, [watchtower])
		self.player1.buy_card("Silver")
		#0 buys should end turn normally but we have a reaction so should still be player1's turn
		self.assertTrue(self.game.get_turn_owner().name == self.player1.name)

		self.player1.exec_commands({"command":"post_selection", "selection":["Reveal"]})
		self.player1.exec_commands({"command":"post_selection", "selection":["Put on top of deck"]})
		self.assertTrue(len(self.player1.discard_pile) == 0)
		self.assertTrue(self.player1.deck[-1].title == "Silver")

		self.player1.end_turn()
		witch = base.Witch(self.game, self.player2)
		self.player2.hand.add(witch)
		watchtower2 = prosperity.Watchtower(self.game, self.player1)
		self.player1.hand.add(watchtower2)

		witch.play()
		self.player1.exec_commands({"command":"post_selection", "selection":["Reveal"]})
		self.player1.exec_commands({"command":"post_selection", "selection":["Trash"]})
		self.assertTrue(self.game.trash_pile[-1].title == "Curse")

	def test_Kings_Court(self):
		tu.print_test_header("testing King's Court")
		conspirator = intrigue.Conspirator(self.game, self.player1)
		kings_court = prosperity.Kings_Court(self.game, self.player1)
		tu.set_player_hand(self.player1, [conspirator, kings_court])
		kings_court.play()
		tu.send_input(self.player1, "post_selection", ["Conspirator"])
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(self.player1.balance == 6)
		#conspirator should be triggered twice, we drew 2 cards
		self.assertTrue(len(self.player1.hand) == 2)
		self.player1.end_turn()
		conspirators_in_deck = [x for x in self.player1.all_cards() if x.title == "Conspirator"]
		self.assertTrue(len(conspirators_in_deck) == 1)

	def test_Mint(self):
		tu.print_test_header("test Mint")
		mint = prosperity.Mint(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)

		mint.play()

		self.assertTrue(self.player1.discard_pile[0].title == "Copper")

		self.player1.hand.add(silver)
		self.player1.hand.add(silver)
		mint.play()
		tu.send_input(self.player1, "post_selection", ["Silver"])
		self.assertTrue(self.player1.discard_pile[1].title == "Silver")

		self.player1.spend_all_money()
		self.player1.buy_card('Mint')
		self.assertTrue(len(self.game.trash_pile) >= 5)

	def test_Mountebank(self):
		tu.print_test_header("test Mountebank")
		mountebank = prosperity.Mountebank(self.game, self.player1)
		curse = crd.Curse(self.game, self.player2)

		self.player2.hand.add(curse)

		mountebank.play()

		self.assertTrue(self.player1.balance == 2)
		tu.send_input(self.player2, "post_selection", ["Yes"])

		self.assertTrue(self.player2.discard_pile[0].title == "Curse")
		#curse is gained first then copper
		self.assertTrue(self.player3.discard_pile[0].title == "Curse")
		self.assertTrue(self.player3.discard_pile[1].title == "Copper")

	def test_Bishop(self):
		tu.print_test_header("test Bishop")
		bishop = prosperity.Bishop(self.game, self.player1)
		steward = intrigue.Steward(self.game, self.player1)
		self.player1.hand.add(steward)

		bishop.play()
		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(self.player1.vp == 1)

		tu.send_input(self.player1, "post_selection", ["Steward"])

		self.assertTrue(self.player1.vp == 2)
		tu.send_input(self.player2, "post_selection", ["None"])
		tu.send_input(self.player3, "post_selection", ["Copper"])

		self.assertTrue(self.player3.vp == 0)
		self.assertTrue(len(self.player3.hand.card_array()) == 4)
		self.assertTrue(len(self.player2.hand.card_array()) == 5)

	def test_Forge(self):
		tu.print_test_header("test Forge")
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
		tu.send_input(self.player1, "post_selection", ["Steward", "Copper", "Copper", "Minion"])
		self.assertTrue(len(self.game.trash_pile) == 4)
		tu.send_input(self.player1, "selectSupply", ["Province"])
		self.assertTrue(self.player1.discard_pile[0].title == "Province")

		forge.play()
		# trash prices total to 13 -- nothing to gain
		tu.send_input(self.player1, "post_selection", ["Torturer", "Secret Chamber", "Gold"])
		self.assertTrue(self.player1.waiting["cb"] is None)

	def test_City(self):
		tu.print_test_header("test City")
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
		tu.print_test_header("test Loan")
		loan = prosperity.Loan(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)

		self.player1.deck.append(estate)
		self.player1.deck.append(estate)
		self.player1.deck.append(estate)

		loan.play()

		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(len(self.player1.discard_pile) >= 3)
		tu.send_input(self.player1, "post_selection", ["Trash"])
		self.assertTrue(len(self.game.trash_pile) == 1)
		self.assertTrue("Treasure" in self.game.trash_pile[-1].type)


	def test_Venture(self):
		tu.print_test_header("test Venture")
		venture = prosperity.Venture(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		loan = prosperity.Loan(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)
		self.player1.deck += [loan, estate, estate, silver, estate]

		venture.play()

		self.assertTrue(len(self.player1.discard_pile) == 1)
		self.assertTrue(self.player1.balance == 3)

		venture.play()

		# self.assertTrue(len(self.player1.discard_pile) == 4)
		self.assertTrue(self.player1.balance == 5)
		self.assertTrue(silver in self.player1.all_cards())

	def test_Vault(self):
		tu.print_test_header("testing vault")
		vault = prosperity.Vault(self.game, self.player1)
		self.player1.hand.add(vault)

		vault.play()
		tu.send_input(self.player1, "post_selection", ["Estate", "Estate"])
		#add two coppers to player2's hand so he can use vault to discard
		tu.add_many_to_hand(self.player2, crd.Copper(self.game, self.player2), 2)
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		#both players should be able to choose to discard at the same time
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		self.assertTrue(self.player3.last_mode["mode"] == "select")
		tu.send_input(self.player2, "post_selection", ["Yes"])		
		cards_in_hand = len(self.player2.hand.card_array())
		tu.send_input(self.player2, "post_selection", ["Copper", "Copper"])
		self.assertTrue(len(self.player2.hand.card_array()) == cards_in_hand - 1)

		self.player3.exec_commands({"command":"post_selection", "selection":["No"]})
		self.assertTrue(self.player1.last_mode["mode"] == "buy")

	def test_Bank(self):
		tu.print_test_header("test Bank")
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
		tu.print_test_header("test Hoard")
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
		tu.print_test_header("test Talisman")
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
		tu.print_test_header("test Goons")
		goons = prosperity.Goons(self.game, self.player1)
		self.player1.hand.add(goons)
		self.player1.hand.add(goons)

		self.player1.actions = 2

		goons.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.buys == 2)
		tu.send_input(self.player2, "post_selection", ["Copper", "Copper"])
		tu.send_input(self.player3, "post_selection", ["Copper", "Copper"])

		goons.play()

		self.player1.buy_card("Copper")
		self.assertTrue(self.player1.vp == 2)
		self.player1.buy_card("Copper")
		self.player1.buy_card("Copper")
		self.assertTrue(self.player1.vp == 6)

	def test_Rabble(self):
		tu.print_test_header("test Rabble")
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
		tu.send_input(self.player3, "post_selection", ["Gardens", "Duchy"])

		topdeck1 = self.player3.topdeck()
		topdeck2 = self.player3.topdeck()

		self.assertTrue(topdeck1.title == "Duchy")
		self.assertTrue(topdeck2.title == "Gardens")

	def test_Royal_Seal(self):
		tu.print_test_header("test Royal Seal")
		royal_seal = prosperity.Royal_Seal(self.game, self.player1)
		workers_village = prosperity.Workers_Village(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.add(royal_seal)
		self.player1.hand.add(copper)
		tu.add_many_to_hand(self.player1, workers_village, 3)

		workers_village.play()
		workers_village.play()
		workers_village.play()

		royal_seal.play()
		tu.send_input(self.player1, "buyCard", "Curse")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.deck[-1].title == "Curse")
		self.assertTrue(self.player1.last_mode["mode"] == "buy")
		tu.send_input(self.player1, "buyCard", "Silver")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		tu.send_input(self.player1, "post_selection", ["No"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")
		self.assertTrue(self.player1.last_mode["mode"] == "buy")
		tu.send_input(self.player1, "buyCard", "Mint")
		self.assertTrue(self.player1.last_mode["mode"] == "buy")

	def test_quarry(self):
		tu.print_test_header("test Quarry")
		quarry = prosperity.Quarry(self.game, self.player1)
		bridge = intrigue.Bridge(self.game, self.player1)
		self.player1.hand.add(bridge)
		tu.add_many_to_hand(self.player1, quarry, 2)

		bridge.play()
		quarry.play()
		self.assertTrue(self.game.card_from_title("Estate").get_price() == 1)
		self.assertTrue(self.game.card_from_title("Village").get_price() == 0)
		self.assertTrue(self.game.card_from_title("Laboratory").get_price() == 2)
		quarry.play()
		self.assertTrue(self.game.card_from_title("Laboratory").get_price() == 0)
		self.assertTrue(self.player1.balance == 3)
		self.assertTrue(self.player1.last_mode["mode"] == "buy")
		tu.send_input(self.player1, "buyCard", "Laboratory")
		self.assertTrue(self.player1.balance == 3)
		self.player1.end_turn()
		self.assertTrue(self.game.card_from_title("Laboratory").get_price() == 5)

	def test_Peddler(self):
		tu.print_test_header("test Peddler")
		village = base.Village(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.add(copper)
		tu.add_many_to_hand(self.player1, village, 5)

		village.play()
		self.assertTrue(self.game.price_modifier["Peddler"] == 0)
		village.play()
		village.play()
		village.play()
		village.play()
		copper.play()
		self.assertTrue(self.game.price_modifier["Peddler"] == -10)
		self.assertTrue(self.game.card_from_title("Peddler").get_price() == 0)

	def test_Trade_Route(self):
		'''
		This fails currently because our tests are not isolated games and other tests can affect the current state
		'''
		tu.print_test_header("test Trade Route")
		trade_route = prosperity.Trade_Route(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		tu.set_player_hand(self.player1, [trade_route, copper, copper, copper, copper])
		trade_route2 = prosperity.Trade_Route(self.game, self.player2)
		self.player2.hand.add(trade_route2)

		self.assertTrue(self.player1.buys == 1)
		trade_route.play()
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.balance == 0)
		tu.send_input(self.player1, "post_selection", ["Copper"])
		self.player1.spend_all_money()
		#buy 2 estates
		tu.send_input(self.player1, "buyCard", "Estate")
		tu.send_input(self.player1, "buyCard", "Estate")
		self.player1.end_turn()

		tu.send_input(self.player2, "post_selection", ["Copper"])
		self.assertTrue(self.player2.balance == 1)
		self.assertTrue(self.player2.buys == 2)


if __name__ == '__main__':
	unittest.main()