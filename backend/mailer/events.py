import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader, Template, BaseLoader
from mailer.smtp import send_email
import config
from rq import Queue, Connection, Retry
from redis import Redis

redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)

real_path = os.path.abspath('templates')

j_env = Environment(
    loader=FileSystemLoader("./mailer/templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

# Default variables for footer
instance_info = {
    "company_address": config.COMPANY_ADDRESS,
    "unsuscribe_link": config.UNSUSCRIBE_ENDPOINT,
    "copyright": config.COPYRIGHT,
}

def enqueue(fn, *args, **kwargs) -> None:
    if not kwargs.get('description'):
        description = f"An email sending job. Details: {args}"
    with Connection(redis):
        q = Queue('default', connection=redis)
        q.enqueue(fn, args=(args), retry=Retry(max=3, interval=[10, 30, 60]), job_id="Sending email", description=description[:300])


def render_template(template: str, **kwargs):
    template = j_env.get_template(f"{template}.j2")
    render = template.render(**kwargs)
    return render


def register_user(email_to: str, **kwargs) -> None:
    """
    Letter after successful registration
    """
    subject = f"Добро пожаловать, {kwargs['username']}!"
    content = render_template('registration', username=kwargs['username'], **instance_info)
    enqueue(send_email, email_to, subject, content)

def subscription_expired(email_to: str, **kwargs) -> None:
    """
    Sunbscription is expired alrt
    """
    subject = "Ваша подписка закончилась"
    content = render_template('subscription_expired', **instance_info)
    enqueue(send_email, email_to, subject, content)


def successful_payment(email_to: str, **kwargs) -> None:
    """
    Letter after successful payment
    """
    pass




