import unittest
import client as c
import sets.base as base
import sets.intrigue as intrigue
import sets.card as crd
import game as g
import kingdomGenerator as kg

from tornado import gen
import tornado.testing
import tests.test_utils as tu

class TestIntrigue(tornado.testing.AsyncTestCase):
	def setUp(self):
		super().setUp()
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())
		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [], test=True)
		#hard code order of players so that random turn order doesn't interfere with tests
		self.game.players = [self.player1, self.player2, self.player3]
		for i in self.game.players:
			i.game = self.game
		self.game.start_game()
		self.player1.take_turn()

	# --------------------------------------------------------
	# ----------------------- Intrigue -----------------------
	# --------------------------------------------------------

	@tornado.testing.gen_test
	def test_Pawn(self):
		tu.print_test_header("test Pawn")
		pawn = intrigue.Pawn(self.game, self.player1)
		self.player1.hand.add(pawn)
		pawn.play()
		yield tu.send_input(self.player1, "post_selection", ["+$1", "+1 Action"])
		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(self.player1.actions == 1)

	def test_Great_Hall(self):
		tu.print_test_header("test Great Hall")
		great_hall = intrigue.Great_Hall(self.game, self.player1)
		player1_vp = self.player1.total_vp()
		self.player1.hand.add(great_hall)
		great_hall.play()
		self.assertTrue((self.player1.actions == 1))
		self.assertTrue((self.player1.total_vp()) == player1_vp + 1)

	@tornado.testing.gen_test
	def test_Steward(self):
		tu.print_test_header("test Steward")
		steward = intrigue.Steward(self.game, self.player1)
		steward2 = intrigue.Steward(self.game, self.player1)
		steward3 = intrigue.Steward(self.game, self.player1)

		copper = crd.Copper(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		tu.clear_player_hand(self.player1)
		tu.add_many_to_hand(self.player1, steward, 3)
		tu.add_many_to_hand(self.player1, copper, 3)
		tu.add_many_to_hand(self.player1, estate, 2)

		self.player1.actions = 5
		# +$2
		steward.play()
		yield tu.send_input(self.player1, "post_selection", ["+$2"])
		self.assertTrue(self.player1.balance == 2)

		# Trash 2 with more than 2 in hand
		steward2.play()
		trash_size = len(self.game.trash_pile)
		yield tu.send_input(self.player1, "post_selection", ["Trash 2 cards from hand"])
		yield tu.send_input(self.player1, "post_selection", ["Estate", "Estate"])
		self.assertTrue(len(self.game.trash_pile) == trash_size + 2)

		# Trash 2 with homogeneous hand
		steward3.play()
		yield tu.send_input(self.player1, "post_selection", ["Trash 2 cards from hand"])
		self.assertTrue(self.player1.hand.get_count("Copper") == 1)

		self.player1.hand.add(steward)

		# Trash 2 with 1 in hand
		self.player1.hand.data["Steward"] = [intrigue.Steward(self.game, self.player1)]
		steward.play()
		yield tu.send_input(self.player1, "post_selection", ["Trash 2 cards from hand"])
		self.assertTrue(len(self.player1.hand) == 0)

	@tornado.testing.gen_test
	def test_Baron(self):
		tu.print_test_header("test Baron")
		baron = intrigue.Baron(self.game, self.player1)
		tu.clear_player_hand(self.player1)
		tu.add_many_to_hand(self.player1, baron,3)
		estate = crd.Estate(self.game, self.player1)
		# sadly add an estate to hand since no guarantees -- actually overwrites hand
		self.player1.hand.add(estate)
		self.player1.actions = 3

		# decline Estate discard, gain Estate to discard pile.
		baron.play()
		yield tu.send_input(self.player1, "post_selection", ["No"])
		self.assertTrue(self.player1.buys == 2)
		self.assertTrue(len(self.player1.discard_pile) == 1)

		# accept Estate discard, do not gain Estate to discard pile, gain $4
		baron.play()
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.buys == 3)
		self.assertTrue(self.player1.balance == 4)
		self.assertFalse("Estate" in self.player1.hand)

		# Not given option because no Estates in hand.
		baron.play()
		self.assertTrue(self.player1.buys == 4)

	def test_Shanty_Town(self):
		tu.print_test_header("test Shanty Town")
		shanty_town = intrigue.Shanty_Town(self.game, self.player1)
		tu.add_many_to_hand(self.player1, shanty_town,2)

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
		tu.print_test_header("test Conspirator")
		conspirator = intrigue.Conspirator(self.game, self.player1)
		tu.add_many_to_hand(self.player1, conspirator,2)

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

	@tornado.testing.gen_test
	def test_Conspirator_Throne_Room(self):
		tu.print_test_header("test Conspirator Throne Room")
		conspirator = intrigue.Conspirator(self.game, self.player1)
		throne_room = base.Throne_Room(self.game, self.player1)
		tu.set_player_hand(self.player1, [conspirator, throne_room])
		throne_room.play()
		handsize = len(self.player1.hand)
		yield tu.send_input(self.player1, "post_selection", ["Conspirator"])
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.balance == 4)
		#discard conspirator, draw 1 card should have same handsize
		self.assertTrue(handsize == len(self.player1.hand))

	@tornado.testing.gen_test
	def test_Courtyard(self):
		tu.print_test_header("test Courtyard")
		courtyard = intrigue.Courtyard(self.game, self.player1)
		self.player1.hand.add(courtyard)

		cards_in_hand = len(self.player1.hand)

		courtyard.play()
		yield tu.send_input(self.player1, "post_selection", ["Copper"])

		self.assertTrue(len(self.player1.hand) == cards_in_hand + 1)
		topdeck = self.player1.topdeck()
		self.assertTrue(topdeck.title == "Copper")

	@tornado.testing.gen_test
	def test_Nobles(self):
		tu.print_test_header("test Nobles")
		nobles = intrigue.Nobles(self.game, self.player1)
		tu.add_many_to_hand(self.player1, nobles, 2)

		nobles.play()
		yield tu.send_input(self.player1, "post_selection", ["+2 Actions"])
		self.assertTrue(self.player1.actions == 2)

		cards_in_hand = len(self.player1.hand)

		nobles.play()
		yield tu.send_input(self.player1, "post_selection", ["+3 Cards"])
		self.assertTrue(len(self.player1.hand) == cards_in_hand + 2)

	@tornado.testing.gen_test
	def test_Swindler(self):
		tu.print_test_header("test Swindler")
		swindler = intrigue.Swindler(self.game, self.player1)
		self.player2.deck.append(crd.Copper(self.game, self.player2))
		self.player1.hand.add(swindler)

		swindler.play()
		yield tu.send_input(self.player1, "selectSupply", ["Curse"])
		self.assertTrue(self.player2.discard_pile[-1].title == "Curse")


	def test_Duke(self):
		tu.print_test_header("test Duke")
		duke = intrigue.Duke(self.game, self.player1)
		self.player1.hand.add(duke)

		duchy = crd.Duchy(self.game, self.player1)
		self.player1.hand.add(duchy)
		self.player1.deck.append(duchy)
		self.player1.discard_pile.append(duchy)

		self.assertTrue(duke.get_vp() == 3)

	@tornado.testing.gen_test
	def test_Wishing_Well(self):
		tu.print_test_header("test Wishing Well")
		wishing_well = intrigue.Wishing_Well(self.game, self.player1)
		tu.add_many_to_hand(self.player1, wishing_well, 2)
		province = crd.Province(self.game, self.player1)
		self.player1.deck.append(province)
		self.player1.deck.append(crd.Silver(self.game, self.player1))
		self.player1.deck.append(province)

		wishing_well.play()
		yield tu.send_input(self.player1, "selectSupply", ["Curse"])
		yield tu.send_input(self.player1, "selectSupply", ["Province"])
		self.assertTrue(self.player1.hand.get_count('Province') == 1)

		wishing_well.play()
		yield tu.send_input(self.player1, "selectSupply", ["Copper"])
		self.assertTrue(self.player1.hand.get_count('Province') == 1)

	@tornado.testing.gen_test
	def test_Upgrade(self):
		tu.print_test_header("test Upgrade")
		upgrade = intrigue.Upgrade(self.game, self.player1)
		tu.add_many_to_hand(self.player1, upgrade, 2)
		self.player1.hand.add(crd.Copper(self.game, self.player1))
		self.player1.hand.add(crd.Estate(self.game, self.player1))

		upgrade.play()

		yield tu.send_input(self.player1, "post_selection", ["Copper"])
		upgrade.play()
		yield tu.send_input(self.player1, "post_selection", ["Estate"])
		yield tu.send_input(self.player1, "selectSupply", ["Silver"])
		self.assertTrue("Silver" == self.player1.discard_pile[-1].title)

	@tornado.testing.gen_test
	def test_Torturer(self):
		tu.print_test_header("test Torturer")
		torturer = intrigue.Torturer(self.game, self.player1)
		tu.add_many_to_hand(self.player1, torturer, 2)
		self.player1.actions = 2
		tu.send_input(self.player1, "play", "Torturer")
		# choosing to discard 2
		yield tu.send_input(self.player2, "post_selection", ["Discard 2 cards"])
		yield tu.send_input(self.player2, "post_selection", ["Copper", "Copper"])
		yield tu.send_input(self.player3, "post_selection", ["Gain a Curse"])
		self.assertTrue(len(self.player2.hand) == 3)
		tu.send_input(self.player1, "play", "Torturer")
		yield tu.send_input(self.player2, "post_selection", ["Gain a Curse"])
		yield tu.send_input(self.player3, "post_selection", ["Gain a Curse"])
		self.assertTrue(self.player2.hand.get_count('Curse') == 1)

	@tornado.testing.gen_test
	def test_Torturer_Throne_Room(self):
		tu.print_test_header("test Torturer Throne Room")
		throne_room = base.Throne_Room(self.game, self.player1)
		torturer = intrigue.Torturer(self.game, self.player1)
		self.player1.hand.add(torturer)

		throne_room.play()
		#Throne room a torturer
		yield tu.send_input(self.player1, "post_selection", ["Torturer"])
		#Player 2 is choosing, everyone else waits
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue("player2" in self.player1.last_mode["msg"])
		self.assertTrue(self.player3.last_mode["mode"] == "wait")

		yield tu.send_input(self.player2, "post_selection", ["Gain a Curse"])
		#player3's turn to get torturered
		self.assertTrue("player3" in self.player1.last_mode["msg"])
		self.assertTrue(self.player3.last_mode["mode"] != "wait")
		self.assertTrue(self.player2.last_mode["mode"] == "wait")
		self.assertTrue(self.player1.last_mode["mode"] == "wait")

		yield tu.send_input(self.player3, "post_selection", ["Gain a Curse"])
		self.assertTrue("Curse" in self.player3.hand)
		#Second torturer
		yield tu.send_input(self.player2, "post_selection", ["Discard two cards"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		self.assertTrue(self.player3.last_mode["mode"] == "wait")
		yield tu.send_input(self.player2, "post_selection", ["Curse", "Copper"])
		self.assertTrue(self.player3.last_mode["mode"] != "wait")
		yield tu.send_input(self.player3, "post_selection", ["Gain a Curse"])
		self.assertTrue(self.player1.last_mode["mode"] != "wait")

	@tornado.testing.gen_test
	def test_Trading_Post(self):
		tu.print_test_header("test Trading Post")
		trading_post = intrigue.Trading_Post(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		tu.clear_player_hand(self.player1)
		self.player1.hand.add(copper)
		self.player1.hand.add(trading_post)
		self.player1.actions = 3

		yield tu.send_input(self.player1, "play", "Trading Post")
		self.assertTrue(len(self.player1.hand) == 0)

		tu.clear_player_hand(self.player1)
		self.player1.hand.add(copper)
		self.player1.hand.add(copper)
		self.player1.hand.add(trading_post)

		trading_post.play()
		self.assertTrue(self.player1.hand.get_count("Silver") == 1)

		self.player1.hand.add(trading_post)
		self.player1.hand.add(trading_post)
		self.player1.hand.add(trading_post)
		trading_post.play()
		yield tu.send_input(self.player1, "post_selection", ["Trading Post", "Trading Post"])
		self.assertTrue(self.player1.hand.get_count("Silver") == 2)

	@tornado.testing.gen_test
	def test_Ironworks(self):
		tu.print_test_header("test Ironworks")
		ironworks = intrigue.Ironworks(self.game, self.player1)
		tu.add_many_to_hand(self.player1, ironworks, 4)
		self.player1.actions = 2

		tu.send_input(self.player1, "play", "Ironworks")
		yield tu.send_input(self.player1, "selectSupply", ["Steward"])
		self.assertTrue(self.player1.actions == 2)

		tu.send_input(self.player1, "play", "Ironworks")
		yield tu.send_input(self.player1, "selectSupply", ["Silver"])
		self.assertTrue(self.player1.balance == 1)
		self.assertTrue(self.player1.actions == 1)

		tu.send_input(self.player1, "play", "Ironworks")
		cards_in_hand = len(self.player1.hand.card_array())
		yield tu.send_input(self.player1, "selectSupply", ["Great Hall"])
		self.assertTrue(self.player1.actions == 1)
		self.assertTrue(self.player1.hand, cards_in_hand + 1)

	@tornado.testing.gen_test
	def test_Secret_Chamber(self):
		tu.print_test_header("test Secret Chamber")
		secret_chamber = intrigue.Secret_Chamber(self.game, self.player1)
		estate = crd.Estate(self.game, self.player1)
		tu.clear_player_hand(self.player1)

		tu.add_many_to_hand(self.player1, estate, 4)
		self.player1.hand.add(secret_chamber)

		secret_chamber.play()
		yield tu.send_input(self.player1, "post_selection", ["Estate", "Estate", "Estate", "Estate"])
		self.assertTrue(self.player1.balance == 4)
		self.player1.end_turn()
		
		tu.clear_player_hand(self.player1)
		tu.add_many_to_hand(self.player1, estate, 4)
		self.player1.hand.add(secret_chamber)
		#clear player3's hand no reaction
		tu.clear_player_hand(self.player3)

		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.player2.hand.add(base.Militia(self.game, self.player2))

		self.player2.hand.play("Militia")
		yield tu.send_input(self.player1, "post_selection", ["Reveal"])
		self.assertTrue(self.player2.last_mode["mode"] == "wait")
		yield tu.send_input(self.player1, "post_selection", ["Estate", "Estate"])
		yield tu.send_input(self.player1, "post_selection", ["Hide"])
		yield gen.sleep(.2)
		yield tu.send_input(self.player1, "post_selection", ["Estate", "Estate"])
		self.assertTrue(len(self.player1.hand.card_array()) == 3)
		estates = self.player1.hand.get_count("Estate")
		self.player1.draw(2)
		self.assertTrue(self.player1.hand.get_count("Estate") == estates + 2)
		self.assertTrue(self.player2.last_mode["mode"] != "wait")

	def test_Tribute(self):
		tu.print_test_header("test Tribute")
		tribute = intrigue.Tribute(self.game, self.player1)
		tu.add_many_to_hand(self.player1, tribute, 2)
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

	@tornado.testing.gen_test
	def test_Mining_Village(self):
		tu.print_test_header("test Mining Village")
		mining_village = intrigue.Mining_Village(self.game, self.player1)
		mining_village2 = intrigue.Mining_Village(self.game, self.player1)
		self.player1.hand.add(mining_village)
		self.player1.hand.add(mining_village2)

		mining_village.play()
		yield tu.send_input(self.player1, "post_selection", ["No"])
		self.assertTrue(self.player1.actions == 2)
		self.assertTrue(mining_village not in self.game.trash_pile)

		# note discard takes in a string as a parameter so the trashed mining village
		# could be mining_village or mining_village2 it is not guaranteed to be the same
		mining_village2.play()
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.actions == 3)
		self.assertTrue(self.game.trash_pile[-1].title == "Mining Village")
		self.assertTrue(len(self.player1.played)==1)
		self.assertTrue(self.player1.balance == 2)

	@tornado.testing.gen_test
	def test_Mining_Village_Throne_Room(self):
		tu.print_test_header("test Mining Village Throne Room")
		mining_village = intrigue.Mining_Village(self.game, self.player1)
		mining_village2 = intrigue.Mining_Village(self.game, self.player1)
		throne_room = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(mining_village)
		self.player1.hand.add(mining_village2)
		self.player1.hand.add(throne_room)

		throne_room.play()
		yield tu.send_input(self.player1, "post_selection", ["Mining Village"])
		self.assertTrue(self.player1.actions, 2)
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.balance == 2)
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertTrue(self.player1.balance == 2)

	def test_Bridge(self):
		tu.print_test_header("test Bridge")
		bridge = intrigue.Bridge(self.game, self.player1)
		self.player1.hand.add(bridge)
		bridge.play()
		self.assertTrue(self.player1.balance == 1)
		self.player1.buy_card("Estate")
		self.assertTrue(self.player1.balance == 0)
		self.assertTrue(self.player1.buys == 1)

	def test_Coppersmith(self):
		tu.print_test_header("test Coppersmith")
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

	@tornado.testing.gen_test
	def test_Coppersmith_Throne_Room(self):
		tu.print_test_header("test Coppersmith Throne Room")
		coppersmith = intrigue.Coppersmith(self.game, self.player1)
		throneroom = base.Throne_Room(self.game, self.player1)
		copper = crd.Copper(self.game, self.player1)
		self.player1.hand.add(coppersmith)
		self.player1.hand.add(throneroom)
		self.player1.hand.add(copper)

		throneroom.play()
		yield tu.send_input(self.player1, "post_selection", ["Coppersmith"])
		copper.play()
		self.assertTrue(self.player1.balance == 3)
		#we played throne room, coppersmith, copper
		self.assertTrue(len(self.player1.played) == 3)
		self.player1.end_turn()
		self.assertTrue(copper.value == 1)
		#make sure we only have 1 coppersmith in our deck
		coppersmiths = [x for x in self.player1.all_cards() if x.title == "Coppersmith"]
		self.assertTrue(len(coppersmiths) == 1)

	@tornado.testing.gen_test
	def test_Scout(self):
		tu.print_test_header("test Scout")
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
		yield tu.send_input(self.player1, "post_selection", ["Scout", "Silver"])
		self.assertTrue(self.player1.deck[-1].title == "Silver")
		self.assertTrue(self.player1.deck[-2].title == "Scout")
		#decksize should be 2 less since we took province and great hall out
		self.assertTrue(len(self.player1.deck) == decklength - 2)

	def test_Scout_autoselect(self):
		tu.print_test_header("test Scout autoselect")
		scout = intrigue.Scout(self.game, self.player1)
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.player1.deck.append(crd.Copper(self.game, self.player1))
		self.player1.deck.append(crd.Estate(self.game, self.player1))
		self.player1.deck.append(crd.Estate(self.game, self.player1))
		self.player1.hand.add(scout)

		scout.play()
		self.assertTrue(self.player1.deck[-1].title == "Copper")
		self.assertTrue(self.player1.deck[-2].title == "Copper")

	@tornado.testing.gen_test
	def test_Minion(self):
		tu.print_test_header("test Minion")
		minion = intrigue.Minion(self.game, self.player1)
		self.player1.hand.add(minion)
		moat = base.Moat(self.game, self.player3)
		self.player3.hand.add(moat)
		#top 4 cards of player2's deck will be drawn
		top4 = self.player2.deck[-4:]
		discard_size = len(self.player2.discard_pile)
		minion.play()
		yield tu.send_input(self.player1, "post_selection", ["discard hand and draw 4 cards"])
		yield tu.send_input(self.player3, "post_selection", ["Reveal"])
		yield gen.sleep(.2)
		self.assertTrue(len(self.player1.hand) == 4)
		self.assertTrue(len(self.player2.hand) == 4)
		for x in top4:
			self.assertTrue(x in self.player2.hand.card_array())
		self.assertTrue(discard_size + 5 == len(self.player2.discard_pile))
		self.assertTrue(len(self.player3.hand) > 4)

	@tornado.testing.gen_test
	def test_Minion_Throne_Room(self):
		tu.print_test_header("test Minion Throne Room")
		minion = intrigue.Minion(self.game, self.player1)
		throneroom = base.Throne_Room(self.game, self.player1)
		self.player1.hand.add(minion)
		self.player1.hand.add(throneroom)
		throneroom.play()
		yield tu.send_input(self.player1, "post_selection", ["Minion"])
		yield tu.send_input(self.player1, "post_selection", ["+$2"])
		yield tu.send_input(self.player1, "post_selection", ["discard hand and draw 4 cards"])
		self.assertTrue(len(self.player1.hand) == 4)
		self.assertTrue(self.player1.balance == 2)

	@tornado.testing.gen_test
	def test_Masquerade(self):
		tu.print_test_header("test Masquerade")
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
		yield tu.send_input(self.player1, "post_selection", ["Curse"])
		self.assertTrue(self.player1.hand.get_count("Curse") == 0)

		self.assertTrue(self.player2.hand.get_count("Baron") == 1)
		yield tu.send_input(self.player2, "post_selection", ["Baron"])
		self.assertTrue(self.player2.hand.get_count("Curse") == 1)
		self.assertTrue(self.player2.hand.get_count("Baron") == 0)

		self.assertTrue(self.player3.hand.get_count("Tribute") == 1)
		yield tu.send_input(self.player3, "post_selection", ["Tribute"])
		self.assertTrue(self.player3.hand.get_count("Baron") == 1)
		self.assertTrue(self.player3.hand.get_count("Tribute") == 0)
		self.assertTrue(self.player1.hand.get_count("Tribute") == 1)
		yield tu.send_input(self.player1, "post_selection", ["Tribute"])
		self.assertTrue(self.player1.hand.get_count("Tribute") == 0)

	@tornado.testing.gen_test
	def test_Masquerade_waits(self):
		tu.print_test_header("test Masquerade waits")
		masquerade = intrigue.Masquerade(self.game, self.player1)
		curse = crd.Curse(self.game, self.player1)
		estate = crd.Estate(self.game, self.player2)
		estate3 = crd.Estate(self.game, self.player3)
		self.player1.hand.add(masquerade)
		self.player1.hand.add(curse)
		self.player2.hand.add(estate)
		self.player3.hand.add(estate3)

		masquerade.play()
		yield tu.send_input(self.player1, "post_selection", ["Curse"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player2, "post_selection", ["Estate"])
		self.assertTrue(self.player1.last_mode["mode"] == "wait")
		yield tu.send_input(self.player3, "post_selection", ["Estate"])
		self.assertTrue(self.player1.last_mode["mode"] == "select")

	@tornado.testing.gen_test
	def test_Saboteur(self):
		tu.print_test_header("test Saboteur")
		saboteur = intrigue.Saboteur(self.game, self.player1)
		steward = intrigue.Steward(self.game, self.player2)
		copper = crd.Copper(self.game, self.player2)

		self.player2.deck.append(steward)
		self.player2.deck.append(copper)
		player3_decksize = len(self.player3.deck)

		saboteur.play()

		yield tu.send_input(self.player2, "selectSupply", ["Curse"])

		self.assertTrue(self.player2.discard_pile.pop().title == "Curse")
		self.assertTrue(self.player2.discard_pile.pop().title == "Copper")
		self.assertTrue(len(self.player3.deck) == 0)
		self.assertTrue(player3_decksize == len(self.player3.discard_pile))
		self.player2.deck.append(steward)
		saboteur.play()
		yield tu.send_input(self.player2, "selectSupply", ["None"])
		self.assertTrue(len(self.player2.discard_pile) == 0)

	@tornado.testing.gen_test
	def test_Upgrade_Selection_issue_21(self):
		tu.print_test_header("test Upgrade selection issue 21")
		upgrade = intrigue.Upgrade(self.game, self.player1)
		throne_room = base.Throne_Room(self.game, self.player1)
		self.player1.deck.append(crd.Estate(self.game, self.player1))
		self.player1.deck.append(crd.Silver(self.game, self.player1))

		self.player1.hand.add(upgrade)
		self.player1.hand.add(throne_room)
		throne_room.play()
		yield tu.send_input(self.player1, "post_selection", ["Upgrade"])
		yield tu.send_input(self.player1, "post_selection", ["Silver"])
		yield tu.send_input(self.player1, "selectSupply", ["Coppersmith"])
		self.assertTrue(self.player1.discard_pile[-1].title == "Coppersmith")
		yield tu.send_input(self.player1, "post_selection", ["Estate"])
		yield tu.send_input(self.player1, "selectSupply", ["Silver"])
		
		self.assertTrue(self.player1.discard_pile[-1].title == "Silver")

	@tornado.testing.gen_test
	def test_Mining_Village_Conspirator(self):
		tu.print_test_header("test Mining Village Conspirator")
		mv = intrigue.Mining_Village(self.game, self.player1)
		village = base.Village(self.game, self.player1)
		conspirator = intrigue.Conspirator(self.game, self.player1)
		self.player1.hand.add(mv)
		self.player1.hand.add(village)
		self.player1.hand.add(conspirator)
		village.play()
		mv.play()
		yield tu.send_input(self.player1, "post_selection", ["Yes"])
		self.assertFalse(mv in self.player1.played)
		self.assertTrue(mv in self.game.trash_pile)
		self.assertTrue(self.player1.actions == 3)
		conspirator.play()
		self.assertTrue(self.player1.actions == 3)
		self.player1.exec_commands({"command": "endTurn"})
		self.assertTrue(mv not in self.player1.discard_pile)

if __name__ == '__main__':
	unittest.main()
