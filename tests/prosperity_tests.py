import unittest
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.prosperity as prosperity
import sets.card as crd
import game as g
import kingdomGenerator as kg

import tornado.testing
import tests.test_utils as tu


class TestProsperity(tornado.testing.AsyncTestCase):
	def setUp(self):
		super().setUp()
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [], test=True)
		self.game.players = [self.player1, self.player2, self.player3]
		for i in self.game.players:
			i.game = self.game
		self.game.start_game()
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

	@tornado.testing.gen_test
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
		yield tu.send_input(self.player1, "post_selection", [2])
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

	@tornado.testing.gen_test
	def test_Expand(self):
		tu.print_test_header("testing expand")
		expand = prosperity.Expand(self.game, self.player1)

		expand.play()
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		yield tu.send_input(self.player1, "post_selection", ["Silver"])

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

	@tornado.testing.gen_test
	def test_Watchtower_react(self):
		tu.print_test_header("testing Watchtower reaction")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		tu.set_player_hand(self.player1, [watchtower])
		self.player1.buy_card("Silver")
		#0 buys should end turn normally but we have a reaction so should still be player1's turn
		self.assertTrue(self.game.get_turn_owner().name == self.player1.name)
		#shouldn't trigger reaction wait for opponents
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.last_mode["mode"] != "wait")

		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])
		self.assertTrue(len(self.player1.discard_pile) == 0)
		self.assertTrue(self.player1.deck[-1].title == "Silver")

	@tornado.testing.gen_test
	def test_Watchtower_Witch(self):
		tu.print_test_header("testing Watchtower witch")
		self.player1.end_turn()
		self.assertTrue(self.game.get_turn_owner().name == self.player2.name)

		witch = base.Witch(self.game, self.player2)
		self.player2.hand.add(witch)
		watchtower2 = prosperity.Watchtower(self.game, self.player1)
		self.player1.hand.add(watchtower2)

		witch.play()
		self.assertTrue(self.player2.last_mode["mode"] == "wait")
		self.assertTrue(self.player3.discard_pile[-1].title == "Curse")
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		self.assertTrue(self.player2.last_mode["mode"] == "wait")
		yield tu.send_input(self.player1, "post_selection", ["Trash"])
		self.assertTrue(self.player2.last_mode["mode"] != "wait")
		self.assertTrue(self.game.trash_pile[-1].title == "Curse")

	@tornado.testing.gen_test
	def test_Kings_Court(self):
		tu.print_test_header("testing King's Court")
		conspirator = intrigue.Conspirator(self.game, self.player1)
		kings_court = prosperity.Kings_Court(self.game, self.player1)
		tu.set_player_hand(self.player1, [conspirator, kings_court])
		kings_court.play()
		yield tu.send_input(self.player1, "post_selection", ["Conspirator"])
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(self.player1.balance == 6)
		#conspirator should be triggered twice, we drew 2 cards
		self.assertTrue(len(self.player1.hand) == 2)
		self.player1.end_turn()
		conspirators_in_deck = [x for x in self.player1.all_cards() if x.title == "Conspirator"]
		self.assertTrue(len(conspirators_in_deck) == 1)

	@tornado.testing.gen_test
	def test_Mint(self):
		tu.print_test_header("test Mint")
		mint = prosperity.Mint(self.game, self.player1)
		silver = crd.Silver(self.game, self.player1)
		self.player1.hand.add(mint)
		self.player1.hand.add(silver)
		mint.play()
		yield tu.send_input(self.player1, "post_selection", ["Silver"])
		self.assertTrue(self.player1.discard_pile[0].title == "Silver")
		num_money = len(self.player1.hand.get_cards_by_type("Treasure"))
		self.player1.spend_all_money()
		self.player1.buy_card('Mint')
		self.assertTrue(len(self.game.trash_pile) >= num_money)

	@tornado.testing.gen_test
	def test_Mountebank(self):
		tu.print_test_header("test Mountebank")
		mountebank = prosperity.Mountebank(self.game, self.player1)
		curse = crd.Curse(self.game, self.player2)

		self.player2.hand.add(curse)

		mountebank.play()

		self.assertTrue(self.player1.balance == 2)
		yield tu.send_input(self.player2, "post_selection", ["Yes"])

		self.assertTrue(self.player2.discard_pile[0].title == "Curse")
		#curse is gained first then copper
		self.assertTrue(self.player3.discard_pile[0].title == "Curse")
		self.assertTrue(self.player3.discard_pile[1].title == "Copper")

	@tornado.testing.gen_test
	def test_Bishop(self):
		tu.print_test_header("test Bishop")
		bishop = prosperity.Bishop(self.game, self.player1)
		steward = intrigue.Steward(self.game, self.player1)
		self.player1.hand.add(steward)

		bishop.play()
		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(self.player1.vp == 1)

		yield tu.send_input(self.player1, "post_selection", ["Steward"])

		self.assertTrue(self.player1.vp == 2)
		yield tu.send_input(self.player2, "post_selection", ["None"])
		yield tu.send_input(self.player3, "post_selection", ["Copper"])

		self.assertTrue(self.player3.vp == 0)
		self.assertTrue(len(self.player3.hand.card_array()) == 4)
		self.assertTrue(len(self.player2.hand.card_array()) == 5)

	@tornado.testing.gen_test
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
		yield tu.send_input(self.player1, "post_selection", ["Steward", "Copper", "Copper", "Minion"])
		self.assertTrue(len(self.game.trash_pile) == 4)
		yield tu.send_input(self.player1, "selectSupply", ["Province"])
		self.assertTrue(self.player1.discard_pile[0].title == "Province")

		forge.play()
		# trash prices total to 13 -- nothing to gain
		yield tu.send_input(self.player1, "post_selection", ["Torturer", "Secret Chamber", "Gold"])
		self.assertTrue(self.player1.cb is None)

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

	@tornado.testing.gen_test
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
		yield tu.send_input(self.player1, "post_selection", ["Trash"])
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

	@tornado.testing.gen_test
	def test_Vault(self):
		tu.print_test_header("testing vault")
		vault = prosperity.Vault(self.game, self.player1)
		self.player1.hand.add(vault)

		vault.play()
		yield tu.send_input(self.player1, "post_selection", ["Estate", "Estate"])
		#add two coppers to player2's hand so he can use vault to discard
		tu.add_many_to_hand(self.player2, crd.Copper(self.game, self.player2), 2)
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		#both players should be able to choose to discard at the same time
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		self.assertTrue(self.player3.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Yes"])		
		cards_in_hand = len(self.player2.hand.card_array())
		yield tu.send_input(self.player2, "post_selection", ["Copper", "Copper"])
		self.assertTrue(len(self.player2.hand.card_array()) == cards_in_hand - 1)

		yield tu.send_input(self.player3, "post_selection", ["No"])
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

	@tornado.testing.gen_test
	def test_Goons(self):
		tu.print_test_header("test Goons")
		goons = prosperity.Goons(self.game, self.player1)
		self.player1.hand.add(goons)
		self.player1.hand.add(goons)

		self.player1.actions = 2

		goons.play()
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.buys == 2)
		yield tu.send_input(self.player2, "post_selection", ["Copper", "Copper"])
		yield tu.send_input(self.player3, "post_selection", ["Copper", "Copper"])

		goons.play()

		self.player1.buy_card("Copper")
		self.assertTrue(self.player1.vp == 2)
		self.player1.buy_card("Copper")
		self.player1.buy_card("Copper")
		self.assertTrue(self.player1.vp == 6)

	@tornado.testing.gen_test
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
		yield tu.send_input(self.player3, "post_selection", ["Gardens", "Duchy"])

		topdeck1 = self.player3.topdeck()
		topdeck2 = self.player3.topdeck()

		self.assertTrue(topdeck1.title == "Duchy")
		self.assertTrue(topdeck2.title == "Gardens")

	@tornado.testing.gen_test
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
		yield tu.send_input(self.player1, "buyCard", "Curse")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.deck[-1].title == "Curse")
		self.assertTrue(self.player1.last_mode["mode"] == "buy")
		yield tu.send_input(self.player1, "buyCard", "Silver")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["No"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")
		self.assertTrue(self.player1.last_mode["mode"] == "buy")
		yield tu.send_input(self.player1, "buyCard", "Mint")
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

	@tornado.testing.gen_test
	def test_Forge_Peddler(self):
		tu.print_test_header("test Forge Peddler")
		peddler = prosperity.Peddler(self.game, self.player1)
		self.player1.hand.add(peddler)
		#add one lab to hand
		self.player1.hand.add(base.Laboratory(self.game, self.player1))
		#add forge
		self.player1.hand.add(prosperity.Forge(self.game, self.player1))

		self.assertTrue(self.game.price_modifier["Peddler"] == 0)
		yield tu.send_input(self.player1, "play", "Laboratory")
		self.assertTrue(self.game.price_modifier["Peddler"] == 0)
		yield tu.send_input(self.player1, "play", "Forge")
		self.assertTrue(self.game.card_from_title("Peddler").get_price() == 8)
		yield tu.send_input(self.player1, "post_selection", ["Peddler"])
		self.assertTrue(self.game.card_from_title("Peddler").get_price() == 8)
		yield tu.send_input(self.player1, "post_selection", ["Province"])
		self.player1.spend_all_money()
		self.assertTrue(self.game.card_from_title("Peddler").get_price() == 4)

	@tornado.testing.gen_test
	def test_Trade_Route(self):
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
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		self.player1.spend_all_money()
		#buy 2 estates
		tu.send_input(self.player1, "buyCard", "Estate")
		tu.send_input(self.player1, "buyCard", "Estate")
		self.player1.end_turn()

		trade_route2.play()
		yield tu.send_input(self.player2, "post_selection", ["Copper"])
		self.assertTrue(self.player2.balance == 1)
		self.assertTrue(self.player2.buys == 2)


if __name__ == '__main__':
	unittest.main()