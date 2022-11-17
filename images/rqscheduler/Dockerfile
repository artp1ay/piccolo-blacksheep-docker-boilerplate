FROM python:3.11.0-slim-buster
RUN mkdir /app
WORKDIR /app
RUN pip install rq-scheduler

# CMD ["rqscheduler", "--host", "host.docker.internal", "--port",  "6379", "-v"]
