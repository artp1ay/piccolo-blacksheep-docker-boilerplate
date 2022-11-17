import sys
import logging
from loguru import logger


config = {
	"handlers": [
		{"sink": sys.stdout, "format": "{time} {level} {message}", "level": "DEBUG"},
		{"sink": "app.log", "serialize": False, "format": "{time} {level} {message}"},
	],
}

logger.configure(**config)
logger.enable("piccolo")
logger.enable("blacksheep")
logger.enable("fastapi")
logger.enable("flask")
logger.enable("starlette")
logger.enable("uvicorn")


class InterceptHandler(logging.Handler):
	def emit(self, record):
		try:
			level = logger.level(record.levelname).name
		except ValueError:
			level = record.levelno

		# Find caller from where originated the logged message.
		frame, depth = sys._getframe(6), 6
		while frame and frame.f_code.co_filename == logging.__file__:
			frame = frame.f_back
			depth += 1

		logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


