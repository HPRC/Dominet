import cardpile as cp

def set_player_hand(player, cards):
	player.hand = cp.HandPile(player)
	for x in cards:
		player.hand.add(x)

def print_test_header(msg):
	print(" ---------------------------------------- ")
	print("\t" + msg)
	print(" ---------------------------------------- ")
	
class PlayerHandler():
	def __init__(self):
		self.log = []

	def write_json(self, **kwargs):
		if kwargs["command"] != "announce":
			self.log.append(kwargs)
