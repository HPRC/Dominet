import unittest
import client as c
import sets.base as base
import sets.card as crd
import game as g
import tests.test_utils as tu
import tornado.testing, tornado.ioloop
import waitHandler

class TestWaiter(tornado.testing.AsyncTestCase):
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
		waitHandler.afk_time  = 2

	def test_turn_timeout(self):
		tu.print_test_header("test Turn Timeout")
		self.assertTrue(self.player1.waiter.afk_timer != None)
		self.assertTrue(self.player2.waiter.afk_timer == None)
		self.assertTrue(self.player3.waiter.afk_timer == None)
		self.player1.end_turn()
		self.assertTrue(self.player1.waiter.afk_timer == None)
		self.assertTrue(self.player2.waiter.afk_timer != None)
		self.assertTrue(self.player3.waiter.afk_timer == None)

	def test_reset_afk_timer(self):
		tu.print_test_header("test reset afk timer")
		first_timer = self.player1.waiter.afk_timer
		def player1_spend_money():
			self.assertTrue(self.player1.waiter.afk_timer == first_timer)
			self.player1.exec_commands({"command": "spendAllMoney"})
			self.assertTrue(self.player1.waiter.afk_timer != first_timer)
			self.player1.end_turn()
			self.assertTrue(self.player1.waiter.afk_timer == None)

			def player1_still_timing_afk():
				self.stop()
				self.assertTrue(self.player2.last_mode["mode"] != "select")
			# wait 1 second more than afk time
			self.io_loop.call_later(3, player1_still_timing_afk)

		self.io_loop.call_later(1, player1_spend_money)
		self.wait(timeout=10)

if __name__ == '__main__':
	unittest.main()