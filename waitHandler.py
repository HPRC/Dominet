class WaitHandler():
	def __init__(self, player):
		self.player = player
		# on = list of players waiting for, callback called after select/gain gets response, 
		#locked = false if update waits on callback automatically, true if it will be resolved manually by card
		self.waiting_on = []
		self.msg = ""
		self.locked = False

	def wait(self, msg):
		self.msg = msg
		self.player.write_json(command="updateMode", mode="wait", msg="Waiting for " + self.waiting_on_string() + " " + self.msg)

	def append_wait(self, to_append):
		if not self.is_waiting_on(to_append):
			self.waiting_on.append(to_append)

	def notify(self, notifier):
		if not self.locked:
			if notifier in self.waiting_on:
				self.waiting_on.remove(notifier)
			if not self.is_waiting():
				self.player.update_mode()
			else:
				self.wait("Waiting for " + self.waiting_on_string() + " " + self.msg)

	def setLock(self, lock):
		self.locked = lock

	def update_msg(self, msg):
		self.wait(msg)

	def waiting_on_string(self):
		return ", ".join(list(set(map(lambda x: x.name, self.waiting_on))))

	def is_waiting_on(self, player):
		return player in self.waiting_on

	def is_waiting(self):
		return len(self.waiting_on) > 0