import os
# from dotenv import load_dotenv
#
# load_dotenv()

# Possibly environments: DEV, PROD, TEST
PROJECT_NAME = "Qiobi"
ENVIRONMENT = "DEV"
ALLOWED_HOSTS = ["*"]

DOMAIN = 'qiobi.ru'

# INSTANCE INFO
COMPANY_ADDRESS = '115280, Москва, Ленинская Слобода 19, БЦ "Омега плаза", офис 1'
UNSUSCRIBE_ENDPOINT = "/unsuscribe"
COPYRIGHT = "Все права защищены."

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

# REDIS
REDIS_HOST = "localhost"
REDIS_PORT = 6379

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
SMTP_ENABLED = True
SMTP_DEBUG = True
SMTP_MAIL = "helpdesk@evolan.ru"
SMTP_HOST = "smtp.yandex.ru"
SMTP_LOGIN = "helpdesk@evolan.ru"
SMTP_PORT = 465
SMTP_SSL = True
SMTP_PASSWORD = "clqnthulwbnecwwu"
SMTL_TLS = False

# RabbitMQ
AMQ_ADDRESS="amqp://guest@localhost//"

# Redis
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# CELERY
WORKERS_QTY = 3

# PAYMENTS
PAYMENT_TIMEOUT_HOURS = 24

# YOOKASSA
YOOKASSA_ACCOUNT_ID = "959710"
YOOKASSA_SECRET_KEY = "test_qzWXX0C6IJMAvHlgIwQsG5PaFz_QCGh-g-9KOAUj2XM"
YOOMONEY_REDIRECT_URL = f"https://{DOMAIN}/payment_status"
