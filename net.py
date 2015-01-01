import client as c
import json
import os
from tornado import httpserver, ioloop, web, websocket	
import game as g

HOST = ''
PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"
NUM_PLAYERS = 2


class mainHandler(web.RequestHandler):
	def get(self):
		if (self.get_cookie("DMTusername") != None):
			# self.render("game.html")
			if (self.in_game()):
				self.render("game.html")
			else:
				self.render("lobby.html")
		else:
			self.render(INDEX)

	def post(self):
		#expire_days ~ 30min
		self.set_cookie("DMTusername", str(self.get_argument("username")), expires_days=.02)
		# self.render("game.html")
		if (self.in_game()):
			self.render("game.html")
		else:
			self.render("lobby.html")

	def in_game(self):
		for eg in GameHandler.games:
			if (self.get_cookie("DMTusername") in list(map(lambda x: x.name, eg.players))):
				return True
		return False


class GameHandler(websocket.WebSocketHandler):
	unattachedClients = []
	games = []

	def initialize(self):
		self.client = c.DmClient(self.get_cookie("DMTusername"), self.application.unassigned_id, self)
		self.application.unassigned_id += 1
		self.unattachedClients.append(self.client)

	def write_json(self, **kwargs):
		if not "command" in kwargs:
			print("no command found for " + json.dumps(kwargs))
		return self.write_message(json.dumps(kwargs))		

	def open(self):
		#init client
		self.write_json(command="init", id=self.client.id, name=self.client.name)
		self.chat(self.client.name + " has joined the lobby", None)
		GameHandler.update_lobby();
		if (len(self.unattachedClients) >= NUM_PLAYERS):
			player1 = self.unattachedClients.pop(0)
			player2 = self.unattachedClients.pop(0)
			game = g.DmGame([player1, player2])
			for i in game.players:
				i.game = game
			game.start_game()
			self.games.append(game)

	def chat(self, msg, speaker):
		for i in GameHandler.unattachedClients:
			i.write_json(command="chat", msg=msg, speaker=speaker)

	def update_lobby():
		for i in GameHandler.unattachedClients:
			i.write_json(command="lobby", lobby_list=GameHandler.get_lobby_names())

	def get_lobby_names():
		return list(map(lambda x: x.name, GameHandler.unattachedClients))

	def on_message(self,data):
		jsondata = json.loads(data)
		self.client.exec_commands(jsondata)

	def on_close(self):
		print("\033[94m Socket Closed HELP!\033[0m")

class DmHandler(GameHandler):

	#override
	def open(self):
		#resume on player reconnect
		for each_game in self.games:
			for p in each_game.players:
				if (self.client.name == p.name):
					p.resume_state(self.client)
					self.client.game = p.game
					#update game players
					index = self.client.game.players.index(p)
					self.client.game.players.pop(index)
					self.client.game.players.insert(index, self.client)

					self.client.update_hand()
					self.write_json(command="kingdomCards", data=self.client.game.supply_json(self.client.game.kingdom))
					self.write_json(command="baseCards", data=self.client.game.supply_json(self.client.game.base_supply))

					if (each_game.get_turn_owner() == self.client):
						self.write_json(command="updateMode", mode="action" if self.client.actions > 0 else "buy")
						self.write_json(command="startTurn", actions=self.client.actions, 
							buys=self.client.buys, balance=self.client.balance)
					self.client.game.announce(self.client.name_string() + " has reconnected!")
					for i in self.client.game.players:
						i.write_json(command="updateMode", mode="action" if i.actions > 0 else "buy")
					return
		GameHandler.open(self)
	
	#override
	def on_close(self):
		for i in self.client.game.players:
			if i != self.client:
				i.wait(self.client.name + " has disconnected!")


def main():
	app = web.Application([
		(r'/', mainHandler),
		(r'/ws', DmHandler)
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