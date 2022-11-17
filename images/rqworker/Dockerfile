FROM python:3.11.0-slim-buster
RUN mkdir /app
WORKDIR /app
RUN pip install rq
RUN pip install 'piccolo[postgres]'
# CMD ["rq", "worker", "--with-scheduler", "--url", "redis://host.docker.internal:6379", "-v"]
