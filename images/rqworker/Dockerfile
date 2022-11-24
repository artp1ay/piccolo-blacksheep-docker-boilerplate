FROM python:3.11.0-slim-buster
RUN mkdir /app
WORKDIR /app
RUN apt update
RUN apt install libpq-dev -y
RUN pip install psycopg2-binary rq sqlalchemy 'piccolo[postgres]' piccolo_admin yookassa requests yookassa
