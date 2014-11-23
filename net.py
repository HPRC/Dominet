import sys
import threading
import http.server
import socketserver
import client


PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"
NUM_PLAYERS = 2


class myHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		#mimetypes doesn't need to be global since its only used for get requests
		mimetypes = { "css": "text/css", 
			 "html": "text/html", 
		   "js": "text/javascript"}

		print("Get request for: " + self.path)
		resource = self.__routesHelper(self.path)
		try:
			f = open(resource, "rb")
			data = f.read()
			self.send_response(200)
			self.send_header("Content-type", mimetypes.get(resource.split(".")[1], "text/plain"))
			self.end_headers()
			self.wfile.write(data)
			f.close()
		except:
			print ("404 not found {0}".format(resource))
			self.send_error(404, "ERROR")
		
	def __routesHelper(self, request):
		#File requests 
		if (request.startswith("/")):
			if request == ROOT:
				return INDEX
			else:
				file = request[1:]
				return file

	def do_POST(self):
		print("POST request for: " + self.path)

		if self.path=="/":
			with self.server.serverLock:
				id = self.server.unassigned_id
				self.server.unassigned_id += 1
			c = client.Client(id)
			self.send_response(200)
			self.send_header("Content-type", "text/plain")
			self.end_headers()
			self.wfile.write(str(id).encode())

	def getClient(id):
		with client.Client.clientLock:
			currentClient = client.Client.idMap.get(id)

class asyncHttpServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
  #terminate all spawned threads on exit
  daemon_threads = True
  reuse_address = True
  unassigned_id = 1
  serverLock = threading.Lock()

def start_server():
	server = asyncHttpServer(("", PORT_NUMBER), myHandler)
	print("Server started on " + str(PORT_NUMBER))	
	server.serve_forever()

def main():
	mainThread = threading.Thread(target=start_server)
	mainThread.start()
 
	with client.Client.clientLock:
		while (len(client.Client.unattachedClientList) < NUM_PLAYERS):
			print("Waiting for other player.....")
			client.Client.clientLock.wait()
		print("ABCDEFEEFE")
		connectedClients = client.Client.unattachedClientList
		#unattached clients are now attached
		client.Client.unattachedClientList = [];

		for i,c in connectedClients:
			print(i + " CIDR " + c)



			
if __name__ == "__main__":
  main()