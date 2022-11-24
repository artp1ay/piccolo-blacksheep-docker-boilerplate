import typing as t
import config
import asyncio
from datetime import datetime, timedelta

from piccolo.engine import engine_finder
from yookassa import Configuration, Payment
from mailer.events import subscription_expired

from home.tables import Task
from piccolo.apps.user.tables import BaseUser
from billing.tables import BillingProfile, BillingPlans, Bills, ActiveSubscriptions

from rq import Queue, Connection

# Yookassa
Configuration.account_id = config.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY


# Billing Regular Tasks
async def check_payment_statuses():
    """
    Getting all unpaid bills.
    Periodic: hourly
    """
    unpaid_bills = (
        await Bills.objects()
        .where(Bills.status == Bills.Status.pending)
        .order_by(Bills.created_at)
    )

    for bill in unpaid_bills:
        # Checking if bill payed or not
        payment = Payment.find_one(str(bill.uuid))

        match payment.status:
            case "pending":
                await Bills.update({"holded": True, "in_progress": True}).where(
                    Bills.id == bill.id
                )
            case "succeeded":
                await Bills.update(
                    {
                        "holded": False,
                        "in_progress": False,
                        "payed": True,
                        "payment_data": payment.json(),
                    }
                ).where(Bills.id == bill.id)
            case _:
                print(payment.json())

def cancel_expired_subscriptions():
    """
    Check if subscription expired.
    If expired, update record.
    """
    active_subscriptions = ActiveSubscriptions.update(
        {
            ActiveSubscriptions.status: ActiveSubscriptions.Status.expired
        }
    ).where(
        (ActiveSubscriptions.status == ActiveSubscriptions.Status.active) & (datetime.now() >= ActiveSubscriptions.due_to)
    ).returning(ActiveSubscriptions.id, ActiveSubscriptions.owner).run_sync()

    # Send notification
    if active_subscriptions:
        owner_info = BaseUser.select(BaseUser.email).where(BaseUser.id == active_subscriptions[0]['owner']).first().run_sync()
        subscription_expired(owner_info['email'])


async def cleanup_unpaid_transactions():
    """
    Periodic task.
    Cancel payments which had never been paid a long time.
    """
    timeout = datetime.now() - timedelta(hours=config.PAYMENT_TIMEOUT_HOURS)
    transactions = await Bills.update({Bills.status: Bills.Status.timeout}).where((Bills.last_failed_attempt <= timeout) & (Bills.status == Bills.Status.pending)).returning(
        Bills.id
    )
    print(transactions)
