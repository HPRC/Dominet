from tornado import ioloop, gen

class WaitHandler():
	time_until_afk = 301

	def __init__(self, player):
		self.player = player
		# on = set of player names waiting for, callback called after select/gain gets response, 
		self.waiting_on = set()
		self.msg = ""
		#locked = set of player names we ignore auto updates (and keep waiting) until manually removed from locked set
		self.locked = set()
		self.afk_timer = None
		self.is_afk = False

	def wait(self, msg):
		self.msg = msg
		self.remove_afk_timer()
		for i in self.waiting_on:
			self.player.game.get_player_from_name(i).waiter.reset_afk_timer()
		self.player.write_json(command="updateMode", mode="wait", msg="Waiting for " + self.waiting_on_string() + " " + self.msg)

	def append_wait(self, to_append):
		self.waiting_on.add(to_append.name)

	# need to update mode manually if unlocking
	def notify(self, notifier, unlock=False):
		if self.is_waiting_on(notifier):
			if unlock or not notifier.name in self.locked:
				self.set_lock(notifier, False)
				self.waiting_on.remove(notifier.name)
				notifier.waiter.remove_afk_timer()

				if not self.is_waiting():
					# i'm not waiting, restart timer
					self.reset_afk_timer()
					# if i was not unlocked, called automatically, update mode
					if not unlock:
						self.player.update_mode()
				elif not self.is_waiting_on(self.player):
					self.wait(self.msg)


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

	#should never really be called except for in reset_afk_timer to keep it so that only 1 timer is active per player
	def time_afk(self):
		@gen.coroutine
		def afk_cb():
			self.is_afk = True
			afk_players = [x for x in self.player.game.players if x.waiter.is_afk]
			futures = []
			for i in self.player.get_opponents():
				if i not in afk_players:
					futures.append(i.select(1,1, ["Yes"],
						"{} {} not responded for awhile, force forefeit?".format(", ".join([i.name for i in afk_players]), "have" if len(afk_players) > 1 else "has")))	
			wait_iterator = gen.WaitIterator(*futures)
			while not wait_iterator.done():
				selected = yield wait_iterator.next()
				if selected == ["Yes"]:
					self.player.game.end_game(afk_players)
		self.afk_timer = ioloop.IOLoop.current().call_later(self.time_until_afk, afk_cb)

	def reset_afk_timer(self):
		self.remove_afk_timer()
		self.time_afk()

	def remove_afk_timer(self):
		if self.afk_timer:
			ioloop.IOLoop.instance().remove_timeout(self.afk_timer)
			self.afk_timer = None
			self.is_afk = False

