import os

# Possibly environments: DEV, PROD, TEST
ENVIRONMENT = "DEV"
ALLOWED_HOSTS = ["*"]

# DATABASE
match ENVIRONMENT:
	case 'DEV':
		PG_HOST = "localhost"
		PG_DATABASE = "piccolo_dev"
		PG_USER = "postgres"
		PG_PASSWORD = "password"
		PG_PORT = 5432
	case 'PROD':
		PG_HOST = "localhost"
		PG_DATABASE = "piccolo_prod"
		PG_USER = "postgres"
		PG_PASSWORD = "password"
		PG_PORT = 5432

# SECURITY
SECRET = "7c5bafefc8e8423e0d02a691d45e96fc8d97be55d01042a7e1b56065985bd806"
JWT_SECRET = ""
ALLOWED_IPS = ""

# LOGGING
USE_LOGFILE=True
LOG_ROTATION=False
LOG_ROTATION_RULE="daily"
LOGFILE_PATH="logs"
LOG_LEVEL="DEBUG"

# TELEGRAM
TELEGRAM_ENABLED = False
BOT_TOKEN = ""
ADMIN_CHAT_ID = ""

# SMTP SERVER
SHMTP_ENABLED = True
SMTP_HOST = "smtp.yandex.ru"
SMTP_LOGIN = ""
SMTP_PORT = 25
SMTP_PASSWORD = ""
SMTL_TLS = False

# RabbitMQ
AMQ_ADDRESS="amqp://guest@localhost//"

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379

#CELERY
WORKERS_QTY = 3
