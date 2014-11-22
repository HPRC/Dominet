import sys
import threading
import http.server

PORT_NUMBER = 9999

class myHandler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		print("Get request for: " + self.path)

		if self.path=="/":
			self.path = "index.html"
		elif self.path.startswith("/"):
			self.path = self.path[1:]
		mimetype = { "css": "text/css", "html": "text/html", "js": "text/javascript"}
		try:
			data = open(self.path, "rb").read()
			self.send_response(200)
			self.send_header("Content-type", mimetype.get(self.path.split(".")[1], "text/plain"))
			self.end_headers()
			self.wfile.write(data)
			data.close()
		except:
			print ("404 not found %s", self.path)
			#self.send_error(404, "ERROR")


def start_server():
	server = http.server.HTTPServer(("", PORT_NUMBER), myHandler)
	print("Server started on " + str(PORT_NUMBER))	
	server.serve_forever()

def main():
	mainThread = threading.Thread(target=start_server)
	mainThread.start()

if __name__ == "__main__":
  main()