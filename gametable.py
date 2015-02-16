class GameTable():
	def __init__(self, title, host, seats, sets):
		self.title = title
		self.host = host
		self.seats = seats
		self.sets = sets
		self.players = [host]

	def to_json(self):
		return {
			"title": self.title,
			"host" : self.host.name,
			"seats" : self.seats,
			"players": self.players_string(),
			"sets": self.sets
		}

	def add_player(self, new_player):
		self.players.append(new_player)

	def remove_player(self, player):
		self.players.remove(player);
		if len(self.players) > 0:
			self.host = self.players[0]

	def players_string(self):
		return list(map(lambda x: x.name, self.players))