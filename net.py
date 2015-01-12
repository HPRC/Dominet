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
			self.render("main.html")
		else:
			self.render(INDEX)

	def post(self):
		#expire_days ~ 30min
		self.set_cookie("DMTusername", str(self.get_argument("username")), expires_days=.02)
		self.render("main.html")

	def in_game(self):
		for eg in GameHandler.games:
			if (self.get_cookie("DMTusername") in list(map(lambda x: x.name, eg.players))):
				return True
		return False


class GameHandler(websocket.WebSocketHandler):
	#name => client obj
	unattachedClients = {}
	games = []

	def initialize(self):
		self.client = c.DmClient(self.get_cookie("DMTusername"), self.application.unassigned_id, self)
		self.application.unassigned_id += 1
		self.unattachedClients[self.client.name] = self.client

	def write_json(self, **kwargs):
		if not "command" in kwargs:
			print("no command found for " + json.dumps(kwargs))
		try:
			return self.write_message(json.dumps(kwargs))
		except websocket.WebSocketClosedError:
			print("Tried to write to closed socket")


	def open(self):
		#init client
		self.write_json(command="init", id=self.client.id, name=self.client.name)
		self.chat(self.client.name + " has joined the lobby", None)
		GameHandler.update_lobby()

	def load_game(self, *args):
		game = g.DmGame(list(args))
		for i in game.players:
			i.write_json(command="resume")
			i.game = game
		GameHandler.games.append(game)
		for x in args:
			del GameHandler.unattachedClients[x.name]
		GameHandler.update_lobby()
		GameHandler.announce_lobby(" and ".join(list(map(lambda x: x.name, args))) + " started a game.")


	def chat(self, msg, speaker):
		for name, p in GameHandler.unattachedClients.items():
			p.write_json(command="chat", msg=msg, speaker=speaker)

	def update_lobby():
		for name, p in GameHandler.unattachedClients.items():
			p.write_json(command="lobby", lobby_list=GameHandler.get_lobby_names())

	def get_lobby_names():
		return list(GameHandler.unattachedClients.keys())

	def return_to_lobby(self):
		GameHandler.unattachedClients[self.client.name] = self.client
		GameHandler.update_lobby()
		self.client.game.players.remove(self.client)
		if (len(self.client.game.players) == 0):
			GameHandler.games.remove(self.client.game)

	def on_message(self,data):
		jsondata = json.loads(data)
		self.client.exec_commands(jsondata)
		cmd = jsondata["command"]
		if (cmd == "loadGame"):
			GameHandler.unattachedClients[jsondata["challenger"]].write_json(
				command="gotAccepted")
			self.load_game(*list(map(lambda x: GameHandler.unattachedClients[x], jsondata["players"])))
		elif (cmd == "challenge"):
			GameHandler.unattachedClients[jsondata["otherPlayer"]].write_json(
				command="challenged", challenger=jsondata["challenger"])
		elif (cmd == "cancel"):
			GameHandler.unattachedClients[jsondata["otherPlayer"]].write_json(
				command="unchallenged", challenger=jsondata["challenger"])
		elif (cmd == "decline"):
			GameHandler.unattachedClients[jsondata["challenger"]].write_json(
				command="gotDeclined")

	def announce_lobby(msg):
		for name, p in GameHandler.unattachedClients.items():
			p.write_json(command="announce", msg= msg)

	def on_close(self):
		if (self.client.name in GameHandler.unattachedClients):
			del GameHandler.unattachedClients[self.client.name]
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
					self.write_json(command="init", id=p.id, name=p.name)
					index = self.client.game.players.index(p)
					self.client.game.players.pop(index)
					self.client.game.players.insert(index, self.client)
					self.write_json(command="resume")
					return
		GameHandler.open(self)
	
	#override
	def on_close(self):
		if (self.client.game == None):
			GameHandler.on_close(self)
			return
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