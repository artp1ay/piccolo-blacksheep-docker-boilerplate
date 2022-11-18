import os
# import requests
import sqlalchemy
from sqlalchemy import create_engine

# Init SQLAlchemy connection
engine = create_engine(f"postgresql+psycopg2://{os.getenv('PG_USER', 'postgres')}:{os.getenv('PG_PASSWORD', 'password')}@{os.getenv('PG_HOST', 'localhost')}:{str(os.getenv('PG_PORT', 5432))}/{os.getenv('PG_DB_NAME', 'piccolo_dev')}", echo=True, pool_size=6, max_overflow=10)
engine.connect()

def get_tasks():
	print("huyak")
	return

def insert_task(text: str):
	engine.execute(f"INSERT INTO task values(DEFAULT, '{text}', false);")

class Task:
	def __init__(self):
		self.executor = engine

class StartupTasks(Task):
	pass

class PeriodicTasks(Task):

	def __init__(self):
		super(Task, self).__init__()

	@classmethod
	def insert_task(self, text: str):
		"""
		Inserts task into row
		"""
		engine.execute(f"INSERT INTO task values(DEFAULT, '{text}', false);")
