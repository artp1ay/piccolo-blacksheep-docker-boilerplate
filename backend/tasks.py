# import requests
# from piccolo_conf import DB
# from home.tables import Task
#
# def count_words_at_url(url):
# 	resp = requests.get(url)
# 	return len(resp.text.split())
#
# def get_tasks():
# 	tsk = Task(db=DB).select().order_by(Task.id)
# 	print(tsk)
# 	return tsk


# class PeriodicTasks:
#

from celery import Celery
from celery.schedules import crontab

app = Celery('tasks')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
	# Calls test('hello') every 10 seconds.
	sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')

	# Calls test('world') every 30 seconds
	sender.add_periodic_task(30.0, test.s('world'), expires=10)

	# Executes every Monday morning at 7:30 a.m.
	sender.add_periodic_task(
		crontab(hour=7, minute=30, day_of_week=1),
		test.s('Happy Mondays!'),
	)

@app.task
def add(x, y):
	return x + y
