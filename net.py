import client as c
import json
import os
from tornado import httpserver, ioloop, web, websocket	
import game as g
import gametable as gt

HOST = ''
PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"


class mainHandler(web.RequestHandler):
	def get(self):
		if self.get_cookie("DMTusername") is not None:
			self.render("main.html")
		else:
			self.render(INDEX)

	def post(self):
		self.set_cookie("DMTusername", str(self.get_argument("username")), expires_days=None)
		self.render("main.html")

	def in_game(self):
		for eg in GameHandler.games:
			if self.get_cookie("DMTusername") in list(map(lambda x: x.name, eg.players)):
				return True
		return False


class GameHandler(websocket.WebSocketHandler):
	# name => client obj
	unattachedClients = {}
	games = []
	# host => gametable obj
	game_tables = {}

	def initialize(self):
		self.client = c.DmClient(self.get_cookie("DMTusername"), self.application.unassigned_id, self)
		self.application.unassigned_id += 1
		self.table = None

	def write_json(self, **kwargs):
		if not "command" in kwargs:
			print("no command found for " + json.dumps(kwargs))
		try:
			return self.write_message(json.dumps(kwargs))
		except websocket.WebSocketClosedError:
			print("Tried to write to closed socket")

	def open(self):
		self.unattachedClients[self.client.name] = self.client
		# init client
		self.write_json(command="init", id=self.client.id, name=self.client.name)
		self.chat(self.client.name + " has joined the lobby", None)
		GameHandler.update_lobby()

	def start_game(self, table):
		game = g.DmGame(table.players, table.required, table.excluded, table.supply)
		for i in table.players:
			i.write_json(command="resume")
			i.game = game
		GameHandler.games.append(game)
		for x in table.players:
			del GameHandler.unattachedClients[x.name]
			x.handler.table = None
		del GameHandler.game_tables[table.host.name]
		GameHandler.update_lobby()
		GameHandler.announce_lobby(" and ".join(list(map(lambda x: x.name, table.players))) + " started a game.")


	def chat(self, msg, speaker):
		for name, p in GameHandler.unattachedClients.items():
			p.write_json(command="chat", msg=msg, speaker=speaker)

	def update_lobby():
		for name, p in GameHandler.unattachedClients.items():
			p.write_json(command="lobby", lobby_list=GameHandler.get_lobby_names(), game_tables=GameHandler.get_game_tables())

	def get_lobby_names():
		return list(GameHandler.unattachedClients.keys())

	def get_game_tables():
		tablelist = []
		for host, table in GameHandler.game_tables.items():
			tablelist.append(table)
		return list(map(lambda x: x.to_json(), tablelist))

	def return_to_lobby(self):
		GameHandler.unattachedClients[self.client.name] = self.client
		GameHandler.update_lobby()
		self.client.game.players.remove(self.client)
		if len(self.client.game.players) == 0:
			GameHandler.games.remove(self.client.game)
		else:
			for p in self.client.get_opponents():
				p.write_json(command="chat", msg = self.client.name + " has returned to the lobby.", speaker=None)

	def on_message(self,data):
		jsondata = json.loads(data)
		self.client.exec_commands(jsondata)
		cmd = jsondata["command"]
		if cmd == "createTable":
			self.create_table(jsondata)
		elif cmd == "leaveTable":
			self.leave_table(jsondata)
		elif cmd == "joinTable":
			self.join_table(jsondata)
		elif cmd == "startGame":
			table = GameHandler.game_tables[jsondata["host"]]
			self.start_game(table)

	def create_table(self, json):
		tableData = json["table"]
		newTable = GameHandler.game_tables[self.client.name] = gt.GameTable(
			tableData["title"], self.client, tableData["seats"], tableData["required"], tableData["excluded"], "Base", tableData["supply"])
		self.table = newTable
		GameHandler.update_lobby()

	def leave_table(self, json):
		table = GameHandler.game_tables[json["host"]]
		self.table = None
		if self.client == table.host:
			# no one left at table
			if len(table.players) == 1:
				del GameHandler.game_tables[json["host"]]
			else:
			# successor host is chosen
				table.remove_player(self.client)
				GameHandler.game_tables[table.host.name] = table
				del GameHandler.game_tables[json["host"]]
		else:
			table.remove_player(self.client)

		GameHandler.update_lobby()

	def join_table(self, json):
		table = GameHandler.game_tables[json["host"]]
		self.table = table
		table.add_player(self.client)
		GameHandler.update_lobby()

	def announce_lobby(msg):
		for name, p in GameHandler.unattachedClients.items():
			p.write_json(command="announce", msg= msg)

	def on_close(self):
		if self.client.name in GameHandler.unattachedClients:
			del GameHandler.unattachedClients[self.client.name]
		if self.table is not None:
			self.leave_table({"host":self.table.host.name})
		GameHandler.update_lobby()
		print("\033[96m " + self.client.name + " has closed the SOCKET! \033[0m")


class DmHandler(GameHandler):

	# override
	def open(self):
		# resume on player reconnect
		print("\033[96m " + self.client.name + " has opened connection \033[0m")
		for each_game in self.games:
			for p in each_game.players:
				if self.client.name == p.name:
					p.resume_state(self.client)
					self.client.game = p.game
					# update game players
					self.write_json(command="init", id=p.id, name=p.name)
					index = self.client.game.players.index(p)
					self.client.game.players.pop(index)
					self.client.game.players.insert(index, self.client)
					self.write_json(command="resume")
					turn_owner = self.client.game.get_turn_owner()
					if self.client.last_mode["mode"] != "gameover":
						for i in self.client.get_opponents():
							if i == turn_owner:
								turn_owner.write_json(command="startTurn", actions=turn_owner.actions, 
								buys=turn_owner.buys, balance=turn_owner.balance)
							i.write_json(**i.last_mode)
					return
		GameHandler.open(self)
	
	# override
	def on_close(self):
		if self.client.game is None:
			GameHandler.on_close(self)
			return
		self.client.ready = False

		# abandoned if everyone left game
		abandoned = True
		for i in self.client.game.players:
			if i.ready is True:
				abandoned = False
		if abandoned:
			GameHandler.games.remove(self.client.game)
			self.client.game = None
		else:
			for i in self.client.game.players:
				if i != self.client:
					if self.client.last_mode["mode"] == "gameover":
						i.write_json(command="announce", msg = self.client.name_string() + " has left.")
					else:
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