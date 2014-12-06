import client
import json
import os
from tornado import httpserver, ioloop, web, websocket	

HOST = ''
PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"
NUM_PLAYERS = 2


class mainHandler(web.RequestHandler):
	def get(self):
		self.render(INDEX)
	def post(self):
		pass

class GameHandler(websocket.WebSocketHandler):
	unattachedClients = []

	def initialize(self):
		self.id = self.application.unassigned_id
		self.application.unassigned_id += 1
		self.unattachedClients.append(self)
		self.game = None

	def write_json(self, **kwargs):
		if not "command" in kwargs:
			print("no command found for " + json.dumps(kwargs))
		return self.write_message(json.dumps(kwargs))		

	def open(self):
		#init client
		self.write_json(command="init", id=self.id)
		if (len(self.unattachedClients) >= NUM_PLAYERS):
			player1 = self.unattachedClients.pop(0)
			player2 = self.unattachedClients.pop(0)
			g = Game([player1, player2])
			for i in g.players:
				i.game = g
			g.start_game()

	def on_message(self,data):
		jsondata = json.loads(data)
		if (jsondata["command"] == "endTurn"):
			self.game.change_turn()

	def take_turn(self):
		self.write_json(command="startTurn")


class Game():
	def __init__(self, players):
		self.players = players
		self.turn = 0

	def start_game(self):
		for i in self.players:
			i.write_json(command="initGame", player1=self.players[0].id, player2=self.players[1].id)
		self.announce("Starting game with " + str(self.players[0].id) + " and " + str(self.players[1].id))
		self.players[self.turn].take_turn()

	def announce(self, msg):
		for i in self.players:
			i.write_json(command="announce", msg=msg)

	def change_turn(self):
		self.turn = (self.turn + 1) % len(self.players)
		self.announce(str(self.players[self.turn].id) + " 's turn !")
		self.players[self.turn].take_turn()


def main():
	app = web.Application([
		(r'/', mainHandler),
		(r'/ws', GameHandler)
	    ],
	    static_path=os.path.join(os.path.dirname(__file__), "static"),
	    debug=True
	    )
	app.unassigned_id = 1

	mainServer = httpserver.HTTPServer(app)
	mainServer.listen(PORT_NUMBER)
	print("server listening on " + str(PORT_NUMBER))
	ioloop.IOLoop.instance().start()

if __name__ == "__main__":
  main()