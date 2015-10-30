from tornado import gen
import momoko
import psycopg2

class Users():

	def __init__(self, conn):
		self.conn = conn

	@gen.coroutine
	def create_table(self):
		yield self.conn.execute("""CREATE TABLE IF NOT EXISTS users 
			(id serial PRIMARY KEY, displayname TEXT UNIQUE, service TEXT, serviceuserid TEXT);""")

	@gen.coroutine
	def create_user(self, username, service, serviceuserid):
		try:
			cursor = yield self.conn.execute("INSERT INTO users (displayname, service, serviceuserid) VALUES (%s, %s, %s)", 
				(username, service, serviceuserid))
			return True
		except psycopg2.Error as err:
			# if unique constraint
			if err.pgcode == "23505":
				if "displayname" in str(err):
					raise Exception("Duplicate Username")
			return False
		
