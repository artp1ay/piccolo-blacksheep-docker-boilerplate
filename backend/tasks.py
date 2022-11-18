import typing as t
import config
import asyncio
from datetime import datetime

from piccolo.engine import engine_finder
from yookassa import Configuration, Payment

from home.tables import Task
from billing.tables import BillingProfile, BillingPlans, Bills

# Yookassa
Configuration.account_id = config.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY

# Billing Regular Tasks
async def check_payment_statuses():
    """
    Getting all unpaid bills.
    Periodic: hourly
    """
    unpaid_bills = await Bills.objects().where(Bills.in_progress == True).order_by(Bills.created_at)

    for bill in unpaid_bills:
        # Checking if bill payed or not
        payment = Payment.find_one(str(bill.uuid))

        match payment.status:
            case 'pending':
                await Bills.update({'holded': True, "in_progress": True}).where(Bills.id == bill.id)
            case 'succeeded':
                await Bills.update({'holded': False, "in_progress": False, "payed": True, "payment_data": payment.json()}).where(Bills.id == bill.id)
            case _:
                print(payment.json())


    # Payment.cancel('21b23b5b-000f-5061-a000-0674e49a8c10')



async def get_tasks_another():
    tq = await Task.select().order_by(Task.id)
    return tq

async def insert_tasks(count: int = 1):
    for count, i in enumerate(range(1, count), start=1):
        await Task.insert(Task(
            name=f"Task number {count}"
        ))

async def edit_tasks():
    queryset = await Task.select().where(Task.completed == False).order_by(Task.id)
    for q in queryset:
        await Task.update({Task.completed: True}).where(Task.id == q['id'])



if __name__ == "__main__":
    asyncio.run(check_payment_statuses())
