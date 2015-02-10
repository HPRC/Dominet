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
			"host" : self.host,
			"seats" : self.seats,
			"players": self.players,
			"sets": self.sets
		}

	def add_player(self, new_player_name):
		self.players.append(new_player_name)

	def remove_player(self, player_name):
		self.players.remove(player_name);
		if len(self.players) > 0:
			self.host = self.players[0]