import cardpile as cp
import sets.base as b
import tornado.gen as gen

def set_player_hand(player, cards):
	player.hand = cp.HandPile(player)
	for x in cards:
		player.hand.add(x)

def clear_player_hand(player):
	set_player_hand(player, [])

def add_many_to_hand(player, card, count):
	if count > 0:
		player.hand.add(card)
	for x in range(1, count):
		new_card_instance = type(card)(player.game, player)
		player.hand.add(new_card_instance)

#simulate input for client selections
@gen.coroutine
def send_input(player, command, selection):
	if command == "post_selection":
		player.exec_commands({"command":command, "selection":selection})
	elif command == "selectSupply" or command == "buyCard" or command == "play":
		player.exec_commands({"command":command, "card":selection})
	#allow executed responses to be yielded after one iteration of the ioloop
	yield gen.moment
		
def print_test_header(msg):
	print("\n ---------------------------------------- ")
	print("\t" + msg)
	print(" ----------------------------------------")
	
class PlayerHandler():
	def __init__(self):
		self.log = []

	def write_json(self, **kwargs):
		if kwargs["command"] != "announce":
			self.log.append(kwargs)
