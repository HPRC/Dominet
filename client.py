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
			print(id)
			Client.clientLock.notify_all()

	def getAction(self):
		return self.queue.get(True)

	def takeTurn(self):
		pid = self.postId()
		pid["turn"] = self.id
		pid["command"] = "startturn"
		self.queue.put(json.dumps(pid).encode())
		with self.postLock:
			while pid["id"] not in self.post_ids:
				self.postLock.wait(timeout=None)
			r = self.post_ids.pop(pid["id"], None)
			print(r)
			print("ASDASDASD")
			return r

	def postId(self):
		post = { "id": self.next_post_id}
		self.next_post_id += 1
		return post

	def announce(self, msg):
		self.queue.put(json.dumps({"command":"announce" ,"msg":msg}).encode())

	def PostResponse(self, data):
		item = json.loads(data.decode())
		id = item.get("id", None)
		print(str(id) + "AA")
		if not id: 
			return
		with self.postLock:
			self.post_ids[id] = item
			self.postLock.notify_all()		


	def endTurn(self):
		self.queue.put(json.dumps({"command": "endTurn", "id":self.id}).encode())