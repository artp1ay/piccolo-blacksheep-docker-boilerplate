from redis import Redis
from rq import Queue

# from rq_scheduler import Scheduler

from datetime import datetime
from datetime import timedelta

# from tasks import count_words_at_url, get_tasks


# Connection
redis = Redis(host="localhost", port=6379)
# scheduler = Scheduler(connection=Redis())

# Queue
queue = Queue(connection=redis)

# Scheduler
# scheduler = Scheduler(connection=redis, queue=queue)

# Periodic Jobs for Scheduler 1
#jobb = scheduler.enqueue_in(timedelta(seconds=5), count_words_at_url, "https://ya.ru")

# job = scheduler.schedule(
#     scheduled_time=datetime.utcnow(),# Time for first execution, in UTC timezone
#     func=count_words_at_url,                     # Function to be queued
#     args=["https://ya.ru"],             # Arguments passed into function when executed
#     # kwargs={'foo': 'bar'},         # Keyword arguments passed into function when executed
#     interval=10,                   # Time before the function is called again, in seconds
#     repeat=10,                     # Repeat this number of times (None means repeat forever)
#     # meta={'foo': 'bar'}            # Arbitrary pickleable data on the job itself
# )

# job = queue.enqueue(print, "helooooowwwwwww")
#queue.enqueue_in(timedelta(seconds=1), count_words_at_url, "https://ya.ru")

# job = queue.enqueue(count_words_at_url, 'http://nvie.com')
job = queue.enqueue(get_tasks)

# worker = Worker(queues=[queue], connection=redis)
# worker.work(with_scheduler=True)


