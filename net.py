import sys
import threading
import http.server

PORT_NUMBER = 9999
ROOT = "/"
INDEX = "index.html"
MIMETYPES = { "css": "text/css", 
						 "html": "text/html", 
						   "js": "text/javascript"}


class myHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		print("Get request for: " + self.path)
		resource = self.__routesHelper(self.path)
		try:
			data = open(resource, "rb").read()
			self.send_response(200)
			self.send_header("Content-type", MIMETYPES.get(resource.split(".")[1], "text/plain"))
			self.end_headers()
			self.wfile.write(data)
			data.close()
		except:
			print ("404 not found {0}".format(resource))
			#self.send_error(404, "ERROR")
		
	def __routesHelper(self, request):
		#File requests 
		if (request.startswith("/")):
			if request == ROOT:
				return INDEX
			else:
				file = request[1:]
				return file

def start_server():
	server = http.server.HTTPServer(("", PORT_NUMBER), myHandler)
	print("Server started on " + str(PORT_NUMBER))	
	server.serve_forever()

def main():
	mainThread = threading.Thread(target=start_server)
	mainThread.start()


			
if __name__ == "__main__":
  main()