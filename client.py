import queue
import threading

class Client:
	clientLock = threading.Condition()
	unattachedClientList = []
	idMap = {}

	def __init__(self, id):
		self.id = id
		#infinite size FIFO queue for storing player actions
		self.queue = queue.Queue(0)
		with Client.clientLock:
			Client.unattachedClientList.append(self)
			Client.idMap[id] = self
			Client.clientLock.notify_all()
