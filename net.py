import client as c
import json
import os
from tornado import httpserver, ioloop, web, websocket	
import card

HOST = ''
PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"
NUM_PLAYERS = 2


class mainHandler(web.RequestHandler):
	def get(self):
		if (self.get_cookie("DMTusername") != None):
			self.render("game.html")
		else:
			self.render(INDEX)

	def post(self):
		#expire_days ~ 30min
		self.set_cookie("DMTusername", str(self.get_argument("username")), expires_days=.02)
		self.render("game.html")

class GameHandler(websocket.WebSocketHandler):
	unattachedClients = []

	def initialize(self):
		self.name = self.get_cookie("DMTusername")
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
		self.write_json(command="init", id=self.id, name=self.name)
		if (len(self.unattachedClients) >= NUM_PLAYERS):
			player1 = self.unattachedClients.pop(0)
			player2 = self.unattachedClients.pop(0)
			g = DmGame([player1, player2])
			for i in g.players:
				i.game = g
			g.start_game()

	def on_message(self,data):
		jsondata = json.loads(data)
		self.exec_commands(jsondata)

	#called before players take their turns
	def setup(self):
		pass

	def take_turn(self):
		self.write_json(command="startTurn")

	def exec_commands(self, data):
		cmd = data["command"]

		if self.game == None:
			return
		if (cmd == "chat"):
			self.game.chat(data["msg"], self.name)

	def on_close(self):
		print("\033[94m Socket Closed HELP!\033[0m")

class Game():
	def __init__(self, players):
		self.players = players
		self.turn = 0

	def chat(self, msg, speaker):
		for i in self.players:
			i.write_json(command="chat", msg=msg, speaker=speaker)

	def start_game(self):
		self.announce("Starting game with " + str(self.players[0].name) + " and " + str(self.players[1].name))
		for i in self.players:
			i.setup()
		self.announce(str(self.players[self.turn].name) + " 's turn !")
		self.players[self.turn].take_turn()

	def announce(self, msg):
		for i in self.players:
			i.write_json(command="announce",msg=msg)

	def change_turn(self):
		self.turn = (self.turn + 1) % len(self.players)
		self.announce("<b>" + str(self.players[self.turn].name) + " 's turn !</b>")
		self.players[self.turn].take_turn()

	def get_turn_owner(self):
		return self.players[self.turn]

class DmGame(Game):
	def __init__(self, players):
		Game.__init__(self, players)
		#kingdom = dictionary {card.title => [card, count]} i.e {"Copper": [card.Copper(self,None),10]}
		self.kingdom = self.init_kingdom([card.Estate(self, None), card.Copper(self, None), 
			card.Silver(self,None), card.Gold(self, None), card.Village(self, None),
			card.Woodcutter(self,None), card.Duchy(self, None), card.Militia(self, None)])

	#override
	def start_game(self):
		for i in self.players:
			i.write_json(command="kingdomCards", data=self.kingdom_json())
		Game.start_game(self)

	def kingdom_json(self):
		kingdom = []
		for title, data in self.kingdom.items():
			card = data[0]
			count = data[1]
			formatCard = card.to_json()
			formatCard["count"] = count
			kingdom.append(formatCard)
		return json.dumps(kingdom)


	def init_kingdom(self, cards):
		kingdom = {}
		for x in cards:
			if (x.type == "Victory"):
				if (len(self.players) ==2):
					kingdom[x.title] = [x,8]
				else:
					kingdom[x.title] = [x,12]
			else:
				kingdom[x.title] = [x,10]
		return kingdom

def main():
	app = web.Application([
		(r'/', mainHandler),
		(r'/ws', c.DmClient)
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