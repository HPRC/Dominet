import client as c
import json
import os
from tornado import httpserver, ioloop, web, websocket, gen
import game as g
import gametable as gt

HOST = ''
PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"


class mainHandler(web.RequestHandler):
	def get(self):
		cookie_name = self.get_cookie("DMTusername")
		if cookie_name is not None:
			self.render("main.html")
		else:
			self.render(INDEX)

	def post(self):
		input_name = str(self.get_argument("username"))
		cookie_name = self.get_cookie("DMTusername")
		#no cookie and no name conflicts
		if not self.application.in_game_or_lobby(input_name) and cookie_name is None:
			self.set_cookie("DMTusername", input_name, expires_days=None)
			self.render("main.html")
		#new user, name conflict
		elif self.application.in_game_or_lobby(input_name) and cookie_name is None:
			self.render(INDEX, error="That username is currently being used!")
		#we have a cookie already 
		elif cookie_name == input_name:
			#in game/lobby with same name and cookie set - resume
			self.render("main.html")
		else:
			#have old name in cookie but requesting new name
			if not self.application.in_game_or_lobby(cookie_name):
				self.set_cookie("DMTusername", input_name, expires_days=None)
				self.render("main.html")
			#trying to play in new tab with new name while connected as another name conflict
			else:
				self.render(INDEX, error="You are already connected!")


class GameHandler(websocket.WebSocketHandler):
	def initialize(self):
		self.application.unassigned_id += 1
		self.table = None
		self.disconnected = False

	def write_json(self, **kwargs):
		if not "command" in kwargs:
			print("no command found for " + json.dumps(kwargs))
		try:
			return self.write_message(json.dumps(kwargs))
		except websocket.WebSocketClosedError:
			print("Tried to write to closed socket")

	def open(self):
		name = self.get_cookie("DMTusername")
		print("\033[96m " + name + " has opened connection \033[0m")
		disconnected = self.application.disconnected_clients()
		if name in disconnected:
			self.client = disconnected[name]
			self.client.handler = self
			self.write_json(command="init", id=self.client.id, name=self.client.name)
			return True
		else:
			self.client = c.DmClient(name, self.application.unassigned_id, self)
			self.application.unattachedClients[self.client.name] = self.client
			# init client
			self.write_json(command="init", id=self.client.id, name=self.client.name)
			self.chat(self.client.name + " has joined the lobby", None)
			self.update_lobby()
			return False

	def start_game(self, table):
		game = g.DmGame(table.players, table.required, table.excluded, table.req_supply)
		for i in table.players:
			i.write_json(command="resume")
			i.game = game
		self.application.games.append(game)
		for x in table.players:
			try:
				del self.application.unattachedClients[x.name]
			except ValueError:
				print("Error tried removing " + x.name + " from unattachedClients list")
			x.handler.table = None
		try:
			del self.application.game_tables[table.host.name]
		except ValueError:
			print("Error tried removing " + table.host.name + "'s table from game_tables list")
		self.update_lobby()
		self.announce_lobby(" and ".join(list(map(lambda x: x.name, table.players))) + " started a game.")

	def chat(self, msg, speaker):
		for name, p in self.application.unattachedClients.items():
			p.write_json(command="chat", msg=msg, speaker=speaker)

	def update_lobby(self):
		for name, p in self.application.unattachedClients.items():
			p.write_json(command="lobby", lobby_list=self.get_lobby_names(), game_tables=self.get_game_tables())

	def get_lobby_names(self):
		return list(self.application.unattachedClients.keys())

	def get_game_tables(self):
		tablelist = []
		for host, table in self.application.game_tables.items():
			tablelist.append(table)
		return list(map(lambda x: x.to_json(), tablelist))

	def return_to_lobby(self):
		self.application.unattachedClients[self.client.name] = self.client
		self.update_lobby()
		self.client.game.players.remove(self.client)
		if len(self.client.game.players) == 0:
			self.application.games.remove(self.client.game)
		else:
			for p in self.client.game.players:
				p.write_json(command="chat", msg = self.client.name + " has returned to the lobby.", speaker=None)
				
	@gen.coroutine
	def on_message(self,data):
		jsondata = json.loads(data)
		# add future to allow exceptions to be printed out
		ioloop.IOLoop.instance().add_future(self.client.exec_commands(jsondata), lambda x: print(x.exception()) if x.exception() else None)
		cmd = jsondata["command"]
		print(self.client.name + " \033[94m" + json.dumps(jsondata) + "\033[0m")

		if cmd == "createTable":
			self.create_table(jsondata)
		elif cmd == "leaveTable":
			self.leave_table(jsondata)
		elif cmd == "joinTable":
			self.join_table(jsondata)
		elif cmd == "startGame":
			if jsondata["host"] not in self.application.game_tables:
				print(self.application.game_tables)
			table = self.application.game_tables[jsondata["host"]]
			self.start_game(table)

	def create_table(self, json):
		tableData = json["table"]
		newTable = self.application.game_tables[self.client.name] = gt.GameTable(
			tableData["title"], self.client, tableData["seats"], tableData["required"], tableData["excluded"], "Base", tableData["req_supply"])
		self.table = newTable
		self.update_lobby()

	def leave_table(self, json):
		table = self.application.game_tables[json["host"]]
		self.table = None
		if self.client == table.host:
			# no one left at table
			if len(table.players) == 1:
				del self.application.game_tables[json["host"]]
			else:
				# successor host is chosen
				table.remove_player(self.client)
				self.application.game_tables[table.host.name] = table
				del self.application.game_tables[json["host"]]
		else:
			table.remove_player(self.client)

		self.update_lobby()

	def join_table(self, json):
		table = self.application.game_tables[json["host"]]
		self.table = table
		table.add_player(self.client)
		self.update_lobby()

	def announce_lobby(self, msg):
		for name, p in self.application.unattachedClients.items():
			p.write_json(command="chat", msg=msg)

	def on_close(self):
		print("\033[96m " + self.client.name + " has closed the SOCKET! \033[0m")
		self.disconnected = True
		if self.client.name in self.application.unattachedClients:
			del self.application.unattachedClients[self.client.name]
		if self.table is not None:
			self.leave_table({"host":self.table.host.name})
		self.update_lobby()


class DmHandler(GameHandler):

	def initialize(self):
		GameHandler.initialize(self)

	# override
	def open(self):
		# resume on player reconnect
		if GameHandler.open(self):
			#resuming
			# update game players
			self.write_json(command="resume")
	
	# override
	def on_close(self):
		GameHandler.on_close(self)
		if self.client.game == None:
			return
		self.client.ready = False
		# check if abandoned (if everyone left game) and remove game if so
		abandoned = True
		for i in self.client.game.players:
			if i.ready is True:
				abandoned = False

		if abandoned:
			self.application.games.remove(self.client.game)
			for i in self.client.game.players:
				i.game = None
				i.waiter.remove_dc_timer()
		else:
			if self.client.last_mode["mode"] == "gameover":
				#remove me from the game
				self.client.game.players.remove(self.client)
				for i in self.client.game.players:
					i.write_json(command="chat", msg = self.client.name + " has left.", speaker=None)
			else:
				self.client.waiter.time_disconnect(0)
		


class DmApplication(web.Application):
	def __init__(self):
		handlers = [
			(r'/', mainHandler),
			(r'/ws', DmHandler)
		]
		settings = {
			"static_path": os.path.join(os.path.dirname(__file__), "static"),
			"debug": True
		}
		#super.init
		web.Application.__init__(self, handlers, **settings)

		self.unassigned_id = 1
		# name => client obj
		self.unattachedClients = {}
		self.games = []
		# host => gametable obj
		self.game_tables = {}


	def in_game_or_lobby(self, name):
		#check if player is in a game
		for eg in self.games:
			if name in list(map(lambda x: x.name, [e for e in eg.players if not e.handler.disconnected])):
				return True
		#check if player is in the lobby
		if name in list(self.unattachedClients.keys()):
			return True
		return False

	#returns dict of name to player object of d/ced players
	def disconnected_clients(self):
		dced = {}
		for eg in self.games:
			for i in [x for x in eg.players if x.handler.disconnected]:
				dced[i.name] = i
		return dced


def main():
	app = DmApplication()

	mainServer = httpserver.HTTPServer(app)
	mainServer.listen(PORT_NUMBER)
	print("server listening on " + str(PORT_NUMBER))
	
	ioloop.IOLoop.instance().start()

if __name__ == "__main__":
  main()