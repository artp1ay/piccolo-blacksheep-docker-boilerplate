import uvicorn
import asyncio
import time

# from redis import Redis
# from rq import Queue, Worker
#
# redis = Redis(host="localhost", port=6379)
# queue = Queue(connection=redis)
# asyncio.create_task(Worker(queue))


if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)



