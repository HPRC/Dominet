import random
class GameTable():
	def __init__(self, title, host, seats, required, excluded, sets, req_supply="default"):
		self.title = title or str(random.randint(0,99999))
		self.host = host
		self.seats = seats
		self.sets = sets
		self.required = required
		self.excluded = excluded
		self.req_supply = req_supply
		self.players = [host]

	def to_json(self):
		return {
			"title": self.title,
			"host": self.host.name,
			"seats": self.seats,
			"players": self.players_string(),
			"required": self.required,
			"excluded": self.excluded,
			"req_supply": self.req_supply,
			"sets": self.sets
		}

	def add_player(self, new_player):
		self.players.append(new_player)

	def remove_player(self, player):
		try:
			self.players.remove(player)
		except ValueError:
			print("mismatch removing {} from {}".format(player, self.players))
			# remove by name instead of client object
			self.players = [x for x in self.players if x.name != player.name]
		if len(self.players) > 0:
			self.host = self.players[0]

	def players_string(self):
		return list(map(lambda x: x.name, self.players))