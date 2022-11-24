import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from smtplib import SMTP, SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Server Config
if config.SMTP_SSL:
    smtp = SMTP_SSL(host=config.SMTP_HOST, port=config.SMTP_PORT)
else:
    smtp = SMTP(host=config.SMTP_HOST, port=config.SMTP_PORT)

if config.SMTP_DEBUG:
    smtp.set_debuglevel(1)

smtp.login(config.SMTP_MAIL, config.SMTP_PASSWORD)


def send_email(to: str, subject: str, body: str):
    if config.SMTP_ENABLED:
        message = MIMEMultipart()
        message['Subject'] = subject
        message['From'] = f"{config.PROJECT_NAME} <{config.SMTP_MAIL}>"
        message['To'] = to

        message.attach(MIMEText(body, "html"))
        msg_body = message.as_string()

        smtp.sendmail(config.SMTP_MAIL, to, msg_body)
        smtp.quit()
