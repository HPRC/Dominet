class WaitHandler():
	def __init__(self, player):
		self.player = player
		# on = list of players waiting for, callback called after select/gain gets response, 
		self.waiting_on = []
		self.msg = ""
		#locked = set of players we ignore auto updates (and keep waiting) until manually removed from locked set
		self.locked = set()

	def wait(self, msg):
		self.msg = msg
		self.player.write_json(command="updateMode", mode="wait", msg="Waiting for " + self.waiting_on_string() + " " + self.msg)

	def append_wait(self, to_append):
		if not self.is_waiting_on(to_append):
			self.waiting_on.append(to_append)

	def notify(self, notifier):
		if not notifier in self.locked:
			if notifier in self.waiting_on:
				self.waiting_on.remove(notifier)
			if not self.is_waiting():
				self.player.update_mode()
			elif not self.waiting_only_myself():
				self.wait(self.msg)

	def set_lock(self, locked_person, locked):
		if locked:
			self.locked.add(locked_person)
		elif locked_person in self.locked:
			self.locked.remove(locked_person)

	def update_msg(self, msg):
		self.wait(msg)

	def waiting_on_string(self):
		return ", ".join(list(set(map(lambda x: x.name, self.waiting_on))))

	def waiting_only_myself(self):
		return len(self.waiting_on) == 1 and self.is_waiting_on(self.player)

	def is_waiting_on(self, player):
		return player in self.waiting_on

	def is_waiting(self):
		return len(self.waiting_on) > 0