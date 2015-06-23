import os

class LogHandler():
	LOGS_DIR = "logs"
	CSS_LINK = "<link rel=\"stylesheet\" href=\"../static/css/bootstrap.min.css\"/>"

	def __init__(self, file_title):
		self.file_title = file_title
		self.flagged = False

	def setup_log_file(self):
		header = "<html><head>" + LogHandler.CSS_LINK + "</head>"
		file = open(self.get_log_file_path(), 'w')
		file.write(header + "\n<h3>" + self.file_title + "</h3><br>")
		file.close()

	def get_log_file_path(self):
		flagged = "flagged_" if self.flagged else ""
		return LogHandler.LOGS_DIR + '/' + flagged + self.file_title + '.html'

	def log_json_data(self, data, sent):
		path = self.get_log_file_path()
		if os.path.exists(path):
			file = open(path, 'a')
			if sent:
				file.write("\n<pre>" + data + "</pre>")
			else:
				file.write("\n<pre><kbd>" + data + "</kbd></pre>")
			file.close()

	def log_html_data(self, data):
		path = self.get_log_file_path()
		if os.path.exists(path):
			file = open(path, 'a')
			file.write("\n" + data + "<br>")
			file.close()

	def rename_log_file(self, new_name):
		# Purpose for this check is because when game ends file path is prefixed with 'finished_'
		# get_log_file_path is naive of this. probably should be adjusted
		if os.path.exists(self.get_log_file_path()):
			os.rename(self.get_log_file_path(), new_name)
			if "finished_" in new_name:
				file = open(path, 'a')
				file.write("</html>")
				file.close()

	def finish_game(self):
		if os.path.exists(self.get_log_file_path()):
			if not self.flagged:
				os.remove(self.get_log_file_path())
			else:
				os.rename(self.get_log_file_path(), LogHandler.LOGS_DIR + "/finished_" + self.file_title + ".html")
		else:
			print("Game ended with no log found at " + self.get_log_file_path())
