import unittest
import client as c
import sets.base as base
import sets.intrigue as intr
import sets.card as crd
import game as g
import tests.test_utils as tu
import tornado.testing, tornado.ioloop, tornado.gen
import waitHandler

class TestWaiter(tornado.testing.AsyncTestCase):
	def setUp(self):
		super().setUp()
		waitHandler.WaitHandler.time_until_afk = 1
		self.player1 = c.DmClient("player1", 0, tu.PlayerHandler())
		self.player2 = c.DmClient("player2", 1, tu.PlayerHandler())
		self.player3 = c.DmClient("player3", 2, tu.PlayerHandler())

		self.game = g.DmGame([self.player1, self.player2, self.player3], [], [], test=True)
		self.game.players = [self.player1, self.player2, self.player3]
		for i in self.game.players:
			i.game = self.game
		self.game.start_game()

	def test_turn_timeout(self):
		tu.print_test_header("test Turn Timeout")
		self.assertTrue(self.player1.waiter.afk_timer != None)
		self.assertTrue(self.player2.waiter.afk_timer == None)
		self.assertTrue(self.player3.waiter.afk_timer == None)
		self.player1.end_turn()
		self.assertTrue(self.player1.waiter.afk_timer == None)
		self.assertTrue(self.player2.waiter.afk_timer != None)
		self.assertTrue(self.player3.waiter.afk_timer == None)
		self.player2.end_turn()
		self.assertTrue(self.player1.waiter.afk_timer == None)
		self.assertTrue(self.player2.waiter.afk_timer == None)
		self.assertTrue(self.player3.waiter.afk_timer != None)
		def player1_and_2_not_afk():
			self.assertTrue(self.player1.waiter.is_afk == False)
			self.assertTrue(self.player1.waiter.afk_timer == None)
			self.assertTrue(self.player2.waiter.is_afk == False)
			self.assertTrue(self.player3.waiter.is_afk)
			self.player3.end_turn()
			self.assertTrue(self.player3.waiter.is_afk == False)
			self.assertTrue(self.player3.waiter.afk_timer == None)
			self.stop()
		self.io_loop.call_later(3, player1_and_2_not_afk)
		self.wait()

	def test_reset_afk_timer(self):
		tu.print_test_header("test reset afk timer")
		first_timer = self.player1.waiter.afk_timer

		def player1_reset_timer():
			self.assertTrue(self.player1.waiter.afk_timer == first_timer)
			self.player1.waiter.reset_afk_timer()
			self.assertTrue(self.player1.waiter.afk_timer != first_timer)
			self.player1.end_turn()
			self.assertTrue(self.player1.waiter.afk_timer == None)

			def player1_still_timing_afk():
				self.assertTrue(self.player1.waiter.is_afk == False)
				self.assertTrue(self.player1.waiter.afk_timer == None)
				self.stop()
			# wait 1 second more than afk time
			self.io_loop.call_later(3, player1_still_timing_afk)

		self.io_loop.call_later(2, player1_reset_timer)
		self.wait(timeout=10)
	
	def test_afk_force_forfeit(self):
		tu.print_test_header("test afk force forefeit")
		self.assertTrue(self.player1.waiter.afk_timer != None)

		def player1_afk():
			self.assertTrue(self.player1.waiter.is_afk)
			self.stop()

		self.io_loop.call_later(4, player1_afk)
		self.wait()

	@tornado.testing.gen_test
	def test_double_wait_timer(self):
		tu.print_test_header("test double wait")
		torturer = intr.Torturer(self.game, self.player1)
		self.player1.hand.add(torturer)
		torturer.play()
		self.assertTrue(self.player2.waiter.afk_timer != None)
		#timer for choosing which torturer method
		initial_timer = self.player2.waiter.afk_timer
		yield tu.send_input(self.player2, "post_selection", ["Discard 2 cards"])
		#timer for choosing which cards to discard
		second_timer = self.player2.waiter.afk_timer
		self.assertTrue(initial_timer != second_timer)
		yield tu.send_input(self.player2, "post_selection", ["Copper", "Copper"])
		self.assertTrue(self.player2.waiter.afk_timer == None)
		yield tornado.gen.sleep(3)
		self.assertTrue(self.player2.waiter.is_afk == False)

if __name__ == '__main__':
	unittest.main()