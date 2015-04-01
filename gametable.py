class GameTable():
	def __init__(self, title, host, seats, required, excluded, sets, supply="default"):
		self.title = title
		self.host = host
		self.seats = seats
		self.sets = sets
		self.required = required
		self.excluded = excluded
		self.supply = supply
		self.players = [host]

	def to_json(self):
		return {
			"title": self.title,
			"host": self.host.name,
			"seats": self.seats,
			"players": self.players_string(),
			"required": self.required,
		    "excluded": self.excluded,
		    "supply": self.supply,
			"sets": self.sets
		}

	def add_player(self, new_player):
		self.players.append(new_player)

	def remove_player(self, player):
		self.players.remove(player)
		if len(self.players) > 0:
			self.host = self.players[0]

	def players_string(self):
		return list(map(lambda x: x.name, self.players))