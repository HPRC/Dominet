import queue
import threading
import json

class Client:
	clientLock = threading.Condition()
	unattachedClientList = []
	idMap = {}

	def __init__(self, id):
		self.id = id
		self.post_ids = {}
		self.postLock = threading.Condition()
		self.next_post_id = 1
		#infinite size FIFO queue for storing player actions
		self.queue = queue.Queue(0)
		with Client.clientLock:
			Client.unattachedClientList.append(self)
			Client.idMap[id] = self
			print(str(id) + " initialized")
			Client.clientLock.notify_all()

	def getAction(self):
		return self.queue.get(True)

	#called before start of first turn
	def initGame(self, players):
		self.queue.put(json.dumps({"command":"initgame" ,"player1": players[0].id, "player2": players[1].id}).encode())

	def takeTurn(self):
		pid = self.postId()
		pid["turn"] = self.id
		pid["command"] = "startturn"
		self.queue.put(json.dumps(pid).encode())
		while(True):
			with self.postLock:
				while pid["id"] not in self.post_ids:
					self.postLock.wait(timeout=None)
				r = self.post_ids.pop(pid["id"], None)
				print(r)
				if (not self.executeClientResponse(r)):
					return

	def executeClientResponse(self, json):
		if (json['action'] == 'endturn'):
			return False
		return True


	def postId(self):
		post = { "id": self.next_post_id}
		self.next_post_id += 1
		return post

	def announce(self, msg):
		self.queue.put(json.dumps({"command":"announce" ,"msg":msg}).encode())

	def PostResponse(self, data):
		item = json.loads(data.decode())
		id = item.get("id", None)
		if not id: 
			return
		with self.postLock:
			self.post_ids[id] = item
			self.postLock.notify_all()		


class DmClient(Client):
	def __init__(self, id):
		Client.__init__(self, id)
		self.discard = []
		self.deck = []
		self.hand = []
		self.actions = 0
		self.buys = 0

	#override
	def takeTurn(self):
		self.actions = 1
		self.buys = 1
		Client.takeTurn(self)

	#override
	def executeClientResponse(self, json):
		if not Client.executeClientResponse(self, json):
			return False
		else:
			# if (json['action'] == 'test'):
			# 	self.buys += 1
			# 	print("\033[94m" + str(self.buys) + "\033[0m")
			return True


