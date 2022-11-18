import config
from redis import Redis
from rq import Queue, Retry

from rq_scheduler import Scheduler

from datetime import datetime
from datetime import timedelta

# from tasks_sqlalchemy import get_tasks, insert_task, PeriodicTasks
from tasks import get_tasks_another, insert_tasks, edit_tasks

import uuid
from loguru import logger

# Logger
logger.add("logs/executor.log", rotation="1 day", enqueue=True)
logger.info("Starting Executor")

# Connection
redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
scheduler = Scheduler(connection=Redis())

# Queue
regular_queue = Queue('default', connection=redis)
periodic_queue = Queue('default', connection=redis)

# Scheduler
periodic_scheduler = Scheduler(connection=redis, queue=periodic_queue)
logger.info("Executor started")

# Periodic Jobs
logger.info("Adding periodic tasks to scheduler begin")
periodic_tasks = [
    # periodic_scheduler.schedule(
    #     scheduled_time=datetime.utcnow(),
    #     func=get_tasks_another,
    #     # kwargs={'foo': 'bar'},
    #     interval=5,
    #     id="Getting List of Tasks",
    #     description = "Get list of tasks periodically"
    # ),
    # periodic_scheduler.schedule(
    #     scheduled_time=datetime.utcnow(),
    #     func=insert_task,
    #     args=[uuid.uuid4().hex],
    #     # kwargs={'foo': 'bar'},
    #     interval=10,
    #     id="Cleaning Caches",
    #     description = "Clean Caches"
    # ),
    # periodic_scheduler.schedule(
    #     scheduled_time=datetime.utcnow(),
    #     func=remove_task,
    #     args=[uuid.uuid4().hex],
    #     # kwargs={'foo': 'bar'},
    #     interval=10,
    #     id="Cleaning Caches",
    #     description = "Clean Caches"
    # ),
]
logger.info(f"Adding periodic tasks to scheduler ends. Added {len(periodic_tasks)} task(s) to scheduler.")

# Regular Jobs
regular_queue.enqueue(insert_tasks, 10, retry=Retry(max=3, interval=[10, 30, 60]), job_id="Inserting Tasks", description="This is spartaaa")

regular_queue.enqueue(edit_tasks, retry=Retry(max=3, interval=[10, 30, 60]), job_id="Edit Task", description="Edit task with ORM")

