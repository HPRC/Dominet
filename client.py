import queue
import threading
import json
'''
DEPRECATED 
'''
class Client:
	clientLock = threading.Condition()
	unattachedClientList = []
	idMap = {}

	def __init__(self, id, s):
		self.id = id
		self.socket = s
		#infinite size FIFO queue for storing player actions
		self.queue = queue.Queue(0)
		with Client.clientLock:
			Client.unattachedClientList.append(self)
			Client.idMap[id] = self
			print(str(id) + " initialized")
			Client.clientLock.notify_all()


class DmClient(Client):
	def __init__(self, id):
		Client.__init__(self, id)
		self.discard = []
		self.deck = []
		self.hand = []
		self.actions = 0
		self.buys = 0

	#override
	def take_turn(self):
		self.actions = 1
		self.buys = 1
		Client.takeTurn(self)

