import config
from redis import Redis
from rq import Queue, Retry
from rq_scheduler import Scheduler
from datetime import datetime
from datetime import timedelta
from tasks import cancel_expired_subscriptions, check_payment_statuses, cleanup_unpaid_transactions
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
    periodic_scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=check_payment_statuses,
        interval=30,
        id="Check Payments",
        description = "Checking payment statuses"
    ),
    periodic_scheduler.schedule(
        scheduled_time=datetime.utcnow(),
        func=cancel_expired_subscriptions,
        interval=60 * 5,
        id="Cancel Expired Subscriptions",
        description = "Cancel expired subscriptions"
    ),
    # periodic_scheduler.schedule(
    #     scheduled_time=datetime.utcnow(),
    #     func=cleanup_unpaid_transactions,
    #     interval=3600 * 12,
    #     id="Cancel Unpaid Subscriptions",
    #     description = "Cancel unpaid subscriptions and change it status."
    # ),
    periodic_scheduler.cron(
        "0 2 * * *",
        func=cleanup_unpaid_transactions,
        id="Cancel Unpaid Subscriptions",
        description = "Cancel unpaid subscriptions and change it status."
    ),
]
logger.info(f"Adding periodic tasks to scheduler ends. Added {len(periodic_tasks)} task(s) to scheduler.")

# Regular Jobs
# regular_queue.enqueue(insert_tasks, 10, retry=Retry(max=3, interval=[10, 30, 60]), job_id="Inserting Tasks", description="This is spartaaa")

#regular_queue.enqueue(edit_tasks, retry=Retry(max=3, interval=[10, 30, 60]), job_id="Edit Task", description="Edit task with ORM")

