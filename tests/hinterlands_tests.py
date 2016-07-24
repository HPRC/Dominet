import unittest
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.hinterlands as hl
import sets.prosperity as prosperity
import sets.supply as supply_cards
import game as g
import kingdomGenerator as kg

import tornado.testing
import tornado.gen as gen

import tests.test_utils as tu


class TestHinterland(tornado.testing.AsyncTestCase):
	def setUp(self):
		super().setUp()
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], kg.all_card_titles(), [], test=True)
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

	@tornado.testing.gen_test
	def test_Crossroads_Throne_Room(self):
		tu.print_test_header("test Crossroads Throne Room")
		crossroads = hl.Crossroads(self.game, self.player1)
		throneroom = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(throneroom)
		self.player1.hand.add(crossroads)
		
		tu.send_input(self.player1, "play", "Throne Room")
		yield tu.send_input(self.player1, "post_selection", ["Crossroads"])
		self.assertTrue(self.player1.actions == 3)

	@tornado.testing.gen_test
	def test_Duchess(self):
		tu.print_test_header("Test Duchess")
		duchess = hl.Duchess(self.game, self.player1)
		self.player1.hand.add(duchess)

		player1top = self.player1.deck[-1]
		player2top = self.player2.deck[-1]
		player3top = self.player3.deck[-1]

		tu.send_input(self.player1, "play", "Duchess")
		self.assertTrue(self.player1.balance == 2)
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		self.assertTrue(self.player3.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Discard"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player2.discard_pile[-1] == player2top)
		self.assertTrue(self.player2.last_mode["mode"] != "select")
		yield tu.send_input(self.player1, "post_selection", ["Put back"])
		self.assertTrue(self.player1.deck[-1] == player1top)
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player3, "post_selection", ["Discard"])
		self.assertTrue(self.player1.last_mode["mode"] != "wait")

		self.player1.end_turn()
		self.player2.balance = 5
		yield tu.send_input(self.player2, "buyCard", "Duchy")
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Yes"])
		self.assertTrue(self.player2.last_mode["mode"] != "select")
		self.assertTrue(self.player2.discard_pile[-1].title == "Duchess")

	@tornado.testing.gen_test
	def test_Develop(self):
		tu.print_test_header("Test Develop")
		develop = hl.Develop(self.game, self.player1)
		tu.add_many_to_hand(self.player1, develop, 2)
		self.player1.hand.add(supply_cards.Copper(self.game, self.player1))
		self.player1.hand.add(supply_cards.Estate(self.game, self.player1))

		develop.play()

		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		develop.play()
		yield tu.send_input(self.player1, "post_selection", ["Estate"])
		yield tu.send_input(self.player1, "selectSupply", ["Silver"])
		self.assertTrue("Silver" == self.player1.discard_pile[-1].title)

	@tornado.testing.gen_test
	def test_Oasis(self):
		tu.print_test_header("Test Oasis")
		oasis = hl.Oasis(self.game, self.player1)
		self.player1.hand.add(oasis)

		initial_balance = self.player1.balance
		initial_hand_size = len(self.player1.hand)
		oasis.play()
		self.assertTrue(self.player1.balance == initial_balance + 1)
		self.assertTrue(self.player1.actions == 1)
		yield tu.send_input(self.player1, "post_selection", ['Copper'])
		self.assertTrue(len(self.player1.hand) == initial_hand_size - 1)
		self.assertTrue(self.player1.discard_pile[-1].title == 'Copper')

	@tornado.testing.gen_test
	def test_Duchess_Feast(self):
		tu.print_test_header("Test Duchess Feast")
		feast = base.Feast(self.game, self.player1)
		self.player1.hand.add(feast)

		tu.send_input(self.player1, "play", "Feast")
		yield tu.send_input(self.player1, "post_selection", ["Duchy"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Duchess")

	@tornado.testing.gen_test
	def test_Trader(self):
		tu.print_test_header("test Trader")
		witch = base.Witch(self.game, self.player1)
		trader = hl.Trader(self.game, self.player2)

		self.player1.hand.add(witch)
		self.player2.hand.add(trader)
		#reaction
		tu.send_input(self.player1, "play", "Witch")
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		self.assertTrue(len(self.game.trash_pile) == 0)
		#and gained a silver
		self.assertTrue(self.player2.discard_pile[-1].title == "Silver")
		yield gen.sleep(.1)
		self.assertTrue(self.player1.last_mode["mode"] != "wait")
		self.assertTrue(self.player3.discard_pile[-1].title == "Curse")
		self.assertTrue(self.game.supply.get_count("Curse") == 19)

		self.player1.end_turn()

		self.player2.hand.add(supply_cards.Estate(self.game, self.player2))
		tu.send_input(self.player2, "play", "Trader")
		yield tu.send_input(self.player2, "post_selection", ["Estate"])
		self.assertTrue(len(self.player2.discard_pile) == 3)

	@tornado.testing.gen_test
	def test_Nomad_Camp(self):
		tu.print_test_header("test Nomad Camp")
		self.player1.hand.add(base.Workshop(self.game, self.player1))
		yield tu.send_input(self.player1, "play", "Workshop")
		yield tu.send_input(self.player1, "post_selection", ["Nomad Camp"])
		self.assertTrue(self.player1.deck[-1].title == "Nomad Camp")

	@tornado.testing.gen_test
	def test_Spice_Merchant(self):
		tu.print_test_header("test Spice Merchant")
		spice_merchant1 = hl.Spice_Merchant(self.game, self.player1)
		spice_merchant2 = hl.Spice_Merchant(self.game, self.player1)
		copper = supply_cards.Copper(self.game, self.player1)
		silver = supply_cards.Silver(self.game, self.player1)
		self.player1.hand.add(spice_merchant1)
		self.player1.hand.add(spice_merchant2)
		self.player1.deck = [silver] * 5
		self.player1.hand.add(copper)
		yield tu.send_input(self.player1, "play", "Spice Merchant")
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		yield tu.send_input(self.player1, "post_selection", ["+2 cards +1 action"])
		self.assertTrue(copper in self.game.trash_pile)
		self.assertTrue(len(self.player1.hand.card_array()) == 8) # We started with 5 cards and then added 2 SMs and a copper (8 cards), then put one in 
		yield tu.send_input(self.player1, "play", "Spice Merchant") # play and trashed the copper, then drew 2 brining us back to 8
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		yield tu.send_input(self.player1, "post_selection", ["+$2 +1 buy"])
		self.assertTrue(len(self.game.trash_pile) == 2)
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(self.player1.balance == 2)


	@tornado.testing.gen_test
	def test_Mandarin(self):
		tu.print_test_header("test Mandarin")
		tu.add_many_to_hand(self.player1, supply_cards.Silver(self.game, self.player1), 3)
		tu.add_many_to_hand(self.player1, supply_cards.Gold(self.game, self.player1), 2)

		tu.send_input(self.player1, "play", "Gold")
		tu.send_input(self.player1, "play", "Silver")
		tu.send_input(self.player1, "play", "Silver")

		yield tu.send_input(self.player1, "buyCard", "Mandarin")
		
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Silver", "Silver", "Gold"])
		self.assertTrue(len(self.player1.played_cards) == 0)
		self.assertTrue(self.player1.deck[-1].title == "Gold")
		self.assertTrue(self.player1.deck[-2].title == "Silver")
		self.assertTrue(self.player1.deck[-3].title == "Silver")

		self.player1.end_turn()
		self.player2.hand.add(hl.Mandarin(self.game, self.player2))
		self.player2.hand.add(supply_cards.Silver(self.game, self.player2))
		tu.send_input(self.player2, "play", "Mandarin")
		self.assertTrue(self.player2.balance == 3)
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		yield tu.send_input(self.player2, "post_selection", ["Copper"])
		self.assertTrue(self.player2.deck[-1].title == "Copper")
		self.assertTrue(len(self.player2.hand) == 5)

	@tornado.testing.gen_test
	def test_duchess_watchtower(self):
		tu.print_test_header("test Duchess Watchtower")
		feast = base.Feast(self.game, self.player1)
		watchtower = prosperity.Watchtower(self.game, self.player1)
		self.player1.hand.add(watchtower)
		self.player1.hand.add(feast)

		tu.send_input(self.player1, "play", "Feast")
		yield tu.send_input(self.player1, "selectSupply", ["Duchy"])
		#choose to gain the duchess
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Duchess")
		#choose to reveal Watchtower
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])

		self.assertTrue(self.player1.deck[-1].title == "Duchess")
		yield tu.send_input(self.player1, "post_selection", ["Hide"])

	@tornado.testing.gen_test
	def test_watchtower_trader(self):
		tu.print_test_header("test Watchtower Trader")
		watchtower = prosperity.Watchtower(self.game, self.player1)
		trader = hl.Trader(self.game, self.player1)
		self.player1.hand.add(watchtower)
		self.player1.hand.add(trader)

		self.player1.spend_all_money()
		yield tu.send_input(self.player1, "buyCard", "Copper")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		#order reactions, reveal trader then watchtower
		yield tu.send_input(self.player1, "post_selection", ["Watchtower", "Trader"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		#reveal trader
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		self.assertTrue(self.game.supply.get_count("Copper") == 30)
		#gaining silver now
		yield tu.send_input(self.player1, "post_selection", ["Watchtower", "Trader"])
		# trader's reaction is ignored since its for silver
		# reveal watchtower
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")

		#watchtower from the copper earlier
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		yield tu.send_input(self.player1, "post_selection", ["Put on top of deck"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")

	@tornado.testing.gen_test
	def test_trader_royal_seal(self):
		tu.print_test_header("test Royal Seal Trader")
		royal_seal = prosperity.Royal_Seal(self.game, self.player1)
		trader = hl.Trader(self.game, self.player1)
		self.player1.hand.add(royal_seal)
		self.player1.hand.add(trader)

		royal_seal.play()
		yield tu.send_input(self.player1, "buyCard", "Copper")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		self.assertTrue(self.game.get_turn_owner() == self.player1)

		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield gen.sleep(.1)
		# royal seal triggers
		self.assertTrue(self.game.get_turn_owner() == self.player1)
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")

	@tornado.testing.gen_test
	def test_Cache(self):
		tu.print_test_header("test Cache")
		yield tu.send_input(self.player1, "buyCard", "Cache")
		self.assertTrue(len(self.player1.discard_pile) == 3)
		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Cache"]) == 1)
		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Copper"]) == 2)

	@tornado.testing.gen_test
	def test_Silk_Road(self):
		tu.print_test_header("test Silk Road")
		silk_road = hl.Silk_Road(self.game, self.player1)
		harem = intrigue.Harem(self.game, self.player1)
		great_hall = intrigue.Great_Hall(self.game, self.player1)
		nobles = intrigue.Nobles(self.game, self.player1)
		gardens = base.Gardens(self.game, self.player1)

		self.player1.hand.add(silk_road)
		self.player1.discard_pile.append(harem)
		self.player1.deck.append(great_hall)

		self.assertTrue(silk_road.get_vp() == 1)

		self.player1.hand.add(gardens)
		self.player1.hand.add(nobles)

		self.assertTrue(silk_road.get_vp() == 2)

	@tornado.testing.gen_test
	def test_Highway(self):
		tu.print_test_header("test Highway")
		highway = hl.Highway(self.game, self.player1)
		workshop = base.Workshop(self.game, self.player1)
		tu.add_many_to_hand(self.player1, highway, 4)
		self.player1.hand.add(workshop)

		tu.send_input(self.player1, "play", "Highway")
		tu.send_input(self.player1, "play", "Highway")
		tu.send_input(self.player1, "play", "Workshop")

		# Gold should cost 4 and should be workshoppable
		yield tu.send_input(self.player1, "selectSupply", ["Gold"])

		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Gold"]) == 1)

	@tornado.testing.gen_test
	def test_Ill_Gotten_Gains(self):
		tu.print_test_header("test Ill-Gotten Gains")
		ill_gotten_gains = hl.Ill_Gotten_Gains(self.game, self.player1)
		self.player1.hand.add(ill_gotten_gains)

		yield tu.send_input(self.player1, "buyCard", "Ill Gotten Gains")
		self.assertTrue(len([x for x in self.player2.discard_pile if x.title == "Curse"]) == 1)
		self.assertTrue(len([x for x in self.player3.discard_pile if x.title == "Curse"]) == 1)

		ill_gotten_gains.play()

		yield tu.send_input(self.player1, "post_selection", ["Yes"])

		self.assertTrue(len(self.player1.hand) == 6)

	@tornado.testing.gen_test
	def test_Border_Village(self):
		tu.print_test_header("test Border Village")
		yield tu.send_input(self.player1, "buyCard", "Border Village")

		yield tu.send_input(self.player1, "selectSupply", ["Duchy"])

		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Border Village"]) == 1)
		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Duchy"]) == 1)

	@tornado.testing.gen_test
	def test_Farmland(self):
		tu.print_test_header("test Farmland")
		yield tu.send_input(self.player1, "buyCard", "Farmland")
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		yield tu.send_input(self.player1, "selectSupply", ["Estate"])
		self.assertTrue(len([x for x in self.player1.discard_pile if x.title == "Estate"]) == 1)

	@tornado.testing.gen_test
	def test_Margrave(self):
		tu.print_test_header("test Margrave")
		margrave = hl.Margrave(self.game, self.player1)
		tu.set_player_hand(self.player1, [margrave])
		margrave.play()
		
		self.assertTrue(len(self.player1.hand)==3)
		self.assertTrue(len(self.player2.hand)==6)
		self.assertTrue(len(self.player3.hand)==6)

		yield tu.send_input(self.player2, "post_selection", ["Copper", "Copper", "Copper"])
		yield tu.send_input(self.player3, "post_selection", ["Copper", "Copper", "Copper"])

		self.assertTrue(len(self.player2.hand)==3)
		self.assertTrue(len(self.player2.discard_pile)==3)
		self.assertTrue(len(self.player3.hand)==3)
		self.assertTrue(len(self.player3.discard_pile)==3)

	@tornado.testing.gen_test
	def test_Embassy(self):
		tu.print_test_header("test Embassy")
		self.player1.balance = 5
		yield tu.send_input(self.player1, "buyCard", "Embassy")
		self.assertTrue(self.player2.discard_pile[-1].title == "Silver")
		self.assertTrue(self.player3.discard_pile[-1].title == "Silver")
		embassy = hl.Embassy(self.game, self.player2)
		copper = supply_cards.Copper(self.game, self.player2)
		tu.set_player_hand(self.player2, [embassy])
		tu.add_many_to_hand(self.player2, copper, 4)
		embassy.play()
		yield tu.send_input(self.player2, "post_selection", ["Copper", "Copper", "Copper"])
		self.assertTrue(len(self.player2.hand) == 6)
	
	@tornado.testing.gen_test
	def test_Scheme(self):
		tu.print_test_header("test Scheme")
		scheme1 = hl.Scheme(self.game, self.player1)
		scheme2 = hl.Scheme(self.game, self.player2)

		tu.add_many_to_hand(self.player1, scheme1, 2)
		self.player2.hand.add(scheme2)

		tu.send_input(self.player1, "play", "Scheme")
		tu.send_input(self.player1, "play", "Scheme")
		self.player1.end_turn()
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		yield tu.send_input(self.player1, "post_selection", ["Scheme", "Scheme"])
		self.assertTrue(self.game.get_turn_owner() == self.player2)
		self.assertTrue(self.player1.hand.get_count("Scheme") == 2)

		tu.send_input(self.player2, "play", "Scheme")

		self.player2.end_turn()
		self.assertTrue(self.player2.last_mode["mode"] == "select")
		self.assertTrue(self.player2.last_mode["max_cards"] == 1)
		yield tu.send_input(self.player2, "post_selection", ["Scheme"])

		self.player3.end_turn()
		self.assertTrue(self.player3.last_mode["mode"] != "select")

	@tornado.testing.gen_test
	def test_Throne_Room_Scheme(self):
		tu.print_test_header("test Throne Room Scheme")
		scheme = hl.Scheme(self.game, self.player1)
		tr = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(scheme)
		self.player1.hand.add(tr)

		tr.play()
		yield tu.send_input(self.player1, "post_selection", ["Scheme"])
		self.player1.end_turn()
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player1.last_mode["max_cards"] == 2)
		yield tu.send_input(self.player1, "post_selection", ["Throne Room", "Scheme"])
		self.assertTrue("Throne Room" in self.player1.hand)
		self.assertTrue("Scheme" in self.player1.hand)
	
	@tornado.testing.gen_test
	def test_Cartographer(self):
		tu.print_test_header("test Cartographer")
		cart = hl.Cartographer(self.game, self.player1)
		village = base.Village(self.game, self.player1)
		silver = supply_cards.Silver(self.game, self.player1)
		self.player1.deck += [village, silver, village, village]
		#draw the gold with cartographer
		self.player1.deck.append(supply_cards.Gold(self.game, self.player1))
		self.player1.hand.add(cart)

		cart.play()
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player1.last_mode["max_cards"] == 4)
		yield tu.send_input(self.player1, "post_selection", ["Village", "Village"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Village")
		self.assertTrue(self.player1.discard_pile[-2].title == "Village")
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue(self.player1.last_mode["max_cards"] == 2)
		yield tu.send_input(self.player1, "post_selection", ["Silver", "Village"])
		
		self.assertTrue(self.player1.deck[-1].title == "Village")
		self.assertTrue(self.player1.deck[-2].title == "Silver")

	@tornado.testing.gen_test
	def test_Oracle(self):
		tu.print_test_header("test Oracle")
		oracle = hl.Oracle(self.game, self.player1)
		curse = supply_cards.Curse(self.game, self.player1)
		self.player1.deck += [curse, curse]
		self.player1.hand.add(oracle)

		deck_size2 = len(self.player2.deck)
		deck_size3 = len(self.player3.deck)
		discard_size2 = len(self.player2.discard_pile)
		discard_size3 = len(self.player3.discard_pile)
		oracle.play()

		yield tu.send_input(self.player1, "post_selection", ["discard"])
		self.assertTrue(curse not in self.player1.deck)
		self.assertTrue(curse in self.player1.discard_pile)

		yield tu.send_input(self.player1, "post_selection", ["keep"])
		self.assertTrue(len(self.player2.deck) == deck_size2)
		self.assertTrue(len(self.player2.discard_pile) == discard_size2)
		yield tu.send_input(self.player1, "post_selection", ["discard"])
		self.assertTrue(len(self.player3.deck) == deck_size3 - 2)
		self.assertTrue(len(self.player3.discard_pile) == discard_size3 + 2)

	@tornado.testing.gen_test
	def test_Haggler(self):
		tu.print_test_header("test Haggler")
		haggler = hl.Haggler(self.game, self.player1)
		self.player1.hand.add(haggler)
		haggler.play()
		self.assertTrue(self.player1.balance == 2)
		self.player1.balance = 8
		self.player1.buys = 2

		tu.send_input(self.player1, "buyCard", "Gold")
		self.assertTrue(self.player1.last_mode["mode"] == "selectSupply")
		yield tu.send_input(self.player1, "post_selection", ["Duchy"])
		self.assertTrue(self.player1.discard_pile[-1].title ==  "Duchy")
		tu.send_input(self.player1, "buyCard", "Estate")
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		self.assertTrue(self.player1.discard_pile[-1].title ==  "Copper")

	@tornado.testing.gen_test
	def test_Stables(self):
		tu.print_test_header("test Stables")
		stables = hl.Stables(self.game, self.player1)
		stables2 = hl.Stables(self.game, self.player1)
		self.player1.hand.add(stables)
		self.player1.deck.append(stables2)
		stables.play()
		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		# original hand of 6 - stables - copper = 4, draw 3 = 7
		self.assertTrue(len(self.player1.hand) == 7)
		self.assertTrue(self.player1.actions == 1)
		stables2.play()
		# nothing happens if you don't discard a treasure
		yield tu.send_input(self.player1, "post_selection", [])
		self.assertTrue(len(self.player1.hand) == 6)
		self.assertTrue(self.player1.actions == 0)

	@tornado.testing.gen_test
	def test_Noble_Brigand(self):
		tu.print_test_header("test Noble Brigand")
		silver = supply_cards.Silver(self.game, self.player2)
		estate = supply_cards.Estate(self.game, self.player3)
		self.player2.deck.append(silver)
		self.player3.deck += [estate, estate]
		nb = hl.Noble_Brigand(self.game, self.player1)
		deck2size = len(self.player2.deck)
		deck3size = len(self.player3.deck)
		nb.play()
		yield tu.send_input(self.player1, "post_selection", ["Silver"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")
		self.assertTrue(len(self.player2.discard_pile) == 1)
		self.assertTrue(len(self.player2.deck) == deck2size - 2)
		self.assertTrue(self.player2.deck[-1].title != "Silver")
		self.assertTrue(len(self.player3.deck) == deck3size - 2)
		self.assertTrue(len(self.player3.discard_pile) == 3)
		self.assertTrue(self.player3.discard_pile[-1].title == "Copper")

	@tornado.testing.gen_test
	def test_Fools_Gold(self):
		tu.print_test_header("test Fool's Gold")
		fg = hl.Fools_Gold(self.game, self.player1)
		tu.clear_player_hand(self.player1)
		tu.add_many_to_hand(self.player1, fg, 3)

		fg2 = hl.Fools_Gold(self.game, self.player3)
		tu.add_many_to_hand(self.player3, fg2, 2)

		yield tu.send_input(self.player1, "play", "Fool's Gold")
		yield tu.send_input(self.player1, "play", "Fool's Gold")
		yield tu.send_input(self.player1, "play", "Fool's Gold")
		self.assertTrue(self.player1.balance == 9)

		yield tu.send_input(self.player1, "buyCard", "Province")
		self.assertTrue(self.player3.last_mode["mode"] == "select")
		self.assertTrue(self.game.get_turn_owner() == self.player1)
		# Trash fool's gold
		yield tu.send_input(self.player3, "post_selection", ["Yes"])
		self.assertTrue(len(self.player3.hand) == 6)
		self.assertTrue(self.player3.deck[-1].title == "Gold")
		self.assertTrue(self.game.trash_pile[-1].title == "Fool's Gold")
		self.assertTrue(self.player3.last_mode["mode"] == "select")
		yield tu.send_input(self.player3, "post_selection", ["Yes"])
		yield tu.send_input(self.player3, "post_selection", ["Yes"])
		self.assertTrue(self.player3.deck[-2].title == "Gold")

	@tornado.testing.gen_test
	def test_Fools_Gold_Trader(self):
		tu.print_test_header("test Fool's Gold Trader")
		fg = hl.Fools_Gold(self.game, self.player2)
		trader = hl.Trader(self.game, self.player2)
		self.player2.hand.add(fg)
		self.player2.hand.add(trader)

		self.player1.balance = 8
		yield tu.send_input(self.player1, "buyCard", "Province")

		# trash fool's gold
		yield tu.send_input(self.player2, "post_selection", ["Yes"])
		# reveal trader
		yield tu.send_input(self.player2, "post_selection", ["Reveal"])
		yield tu.send_input(self.player2, "post_selection", ["Yes"])
		self.assertTrue(self.player2.discard_pile[-1].title == "Silver")
		self.assertTrue(self.game.trash_pile[-1].title == "Fool's Gold")
		self.assertTrue(self.player2.deck[-1].title != "Gold")

	@tornado.testing.gen_test
	def test_inn_gain(self):
		tu.print_test_header("test Inn on gain")
		village = base.Village(self.game, self.player1)
		moat = base.Moat(self.game, self.player1)
		copper = supply_cards.Copper(self.game, self.player1)
		self.player1.discard_pile = [village, moat, copper]

		self.player1.gain('Inn')
		self.assertTrue(self.player1.last_mode["mode"] == "select")
		self.assertTrue("Village" in self.player1.last_mode["select_from"])
		self.assertTrue("Moat" in self.player1.last_mode["select_from"])
		self.assertTrue("Inn" in self.player1.last_mode["select_from"])
		self.assertTrue("Copper" not in self.player1.last_mode["select_from"])
		yield tu.send_input(self.player1, "post_selection", ["Village", "Moat", "Inn"])
		self.assertTrue(self.player1.discard_pile == [copper])
		self.assertTrue(village in self.player1.deck)
		self.assertTrue(moat in self.player1.deck)

	@tornado.testing.gen_test
	def test_tunnel(self):
		tu.print_test_header("test Tunnel")
		tunnel = hl.Tunnel(self.game, self.player1)

		@gen.coroutine
		def should_react_correctly(self):
			self.assertTrue(self.player1.last_mode["mode"] == "select")
			yield tu.send_input(self.player1, "post_selection", ["Reveal"])
			yield gen.sleep(.1)
			self.assertTrue(self.player1.discard_pile[-1].title == "Tunnel")
			self.assertTrue(self.player1.discard_pile[-2].title == "Gold")

		self.player1.discard_floating(tunnel)
		yield should_react_correctly(self)
		self.player1.deck.append(tunnel)
		self.player1.discard_topdeck()
		yield should_react_correctly(self)
		self.player1.hand.add(tunnel)
		self.player1.discard(["Tunnel"], self.player1.discard_pile)
		yield should_react_correctly(self)

if __name__ == '__main__':
	unittest.main()