from tornado import ioloop, gen

class WaitHandler():
	def __init__(self, player):
		self.player = player
		# on = list of player names waiting for, callback called after select/gain gets response, 
		self.waiting_on = []
		self.msg = ""
		#locked = set of player names we ignore auto updates (and keep waiting) until manually removed from locked set
		self.locked = set()
		self.disconnect_timer = None

	def wait(self, msg):
		self.msg = msg
		self.player.write_json(command="updateMode", mode="wait", msg="Waiting for " + self.waiting_on_string() + " " + self.msg)

	def append_wait(self, to_append):
		if not self.is_waiting_on(to_append):
			self.waiting_on.append(to_append.name)

	def notify(self, notifier):
		if not notifier.name in self.locked:
			if self.is_waiting_on(notifier):
				self.waiting_on.remove(notifier.name)
				if not self.is_waiting():
					self.player.update_mode()
				elif not self.is_waiting_on(self.player):
					self.wait(self.msg)

	def handle_reconnect(self, reconnecting_player):
		self.waiting_on.remove(reconnecting_player.name)
		if self.disconnect_timer:
			ioloop.IOLoop.instance().remove_timeout(self.disconnect_timer)
			self.disconnect_timer = None


	def set_lock(self, locked_person, locked):
		if locked:
			self.locked.add(locked_person.name)
		elif locked_person.name in self.locked:
			self.locked.remove(locked_person.name)

	def waiting_on_string(self):
		return ", ".join(self.waiting_on)

	def is_waiting_on(self, player):
		return player.name in self.waiting_on

	def is_waiting(self):
		return len(self.waiting_on) > 0

	@gen.coroutine
	def time_disconnect(self, count):
		count += 1
		if count < 5:
			for i in self.player.get_opponents():
				i.wait(": they have disconnected for {} seconds".format(count), self.player)
			self.disconnect_timer = ioloop.IOLoop.instance().call_later(60, lambda x=count: self.time_disconnect(x))
		else:
			futures = []
			for i in self.player.get_opponents():
				futures.append(i.select(1,1, ["Yes"], "{} has disconnected for over 5 minutes, force forefeit?".format(self.player.name)))
			wait_iterator = gen.WaitIterator(*futures) 
			while not wait_iterator.done():
				selected = yield wait_iterator.next()
				if selected == ["Yes"]:
					self.player.game.end_game([self.player])
