import sys
from subprocess import call
import uuid
import config

import typing as t

from piccolo_admin.endpoints import create_admin
from piccolo_admin.endpoints import TableConfig
from piccolo_api.crud.serializers import create_pydantic_model
from piccolo.engine import engine_finder

from blacksheep import Response, Content
from blacksheep.server import Application
from blacksheep.server.bindings import FromJSON
from blacksheep.server.responses import (
    json,
    status_code,
    bad_request,
    unauthorized,
    not_found,
)
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

from home.endpoints import home
from home.piccolo_app import APP_CONFIG
from piccolo.apps.user.tables import BaseUser
from home.tables import Task
from billing.tables import BillingProfile, BillingPlans, Bills, ActiveSubscriptions

from yookassa import Configuration, Payment
from pprint import pprint
from datetime import datetime, timedelta
from helpers import PaymentsHelper, SubscriptionHelper, return_error
from asyncpg.exceptions import UniqueViolationError

# from q import queue
# from tasks import get_tasks

# Yookassa
Configuration.account_id = config.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY

app = Application(show_error_details=False)

movie_config = TableConfig(BillingProfile, visible_columns=[BillingProfile.id])

app.mount(
    "/admin/",
    create_admin(
        [Task, BillingProfile, BillingPlans, Bills, ActiveSubscriptions]
        # Required when running under HTTPS:
        # allowed_hosts=['my_site.com']
    ),
)

docs = OpenAPIHandler(info=Info(title="Saas Boilerplate API", version="0.0.1"))
docs.bind_app(app)
app.serve_files("static", root_path="/static")
app.router.add_get("/", home)


# Task Handlers
# Hooks for starting and stopping RQ jobs
@app.after_start
async def after_start(application: Application) -> None:
    from executor import periodic_tasks


# @app.on_stop
# async def on_stop(application: Application) -> None:
#     from executor import scheduler
#     for job in periodic_tasks:
#         print(job)
#         scheduler.cancel(job)


TaskModelIn: t.Any = create_pydantic_model(table=Task, model_name="TaskModelIn")
TaskModelOut: t.Any = create_pydantic_model(
    table=Task, include_default_columns=True, model_name="TaskModelOut"
)
TaskModelPartial: t.Any = create_pydantic_model(
    table=Task, model_name="TaskModelPartial", all_optional=True
)

BillsModelOut: t.Any = create_pydantic_model(
    table=Bills,
    model_name="BillsModelOut",
    include_columns=(
        Bills.uuid,
        Bills.created_at,
        Bills.plan,
        Bills.amount,
        Bills.payed,
    ),
)
BillingProfileModelOut: t.Any = create_pydantic_model(
    table=BillingProfile,
    model_name="BillingProfileModelOut",
    exclude_columns=(
        BillingProfile.balance,
        BillingProfile.created_at,
        BillingProfile.updated_at,
        BillingProfile.owner,
    ),
)

UserModelIn: t.Any = create_pydantic_model(
    table=BaseUser,
    model_name="UserModelIn",
    include_columns=(
        BaseUser.username,
        BaseUser.password,
        BaseUser.email,
    ),
)
UserModelOut: t.Any = create_pydantic_model(
    table=BaseUser,
    model_name="UserModelOut",
    include_columns=(BaseUser.username, BaseUser.email, BaseUser.active),
)


@docs(
    summary="Create user with billing profile",
    responses={200: "User created", 400: "User already exists"},
    tags=["Users & Auth"],
)
@app.router.post("/create_user")
async def create_user(user_data: FromJSON[UserModelIn]) -> UserModelOut:
    print(user_data)
    try:
        user = await BaseUser.create_user(**user_data.value.dict(), active=True)
        billing_profile = BillingProfile(owner=user.id)
        if user:
            await billing_profile.save()
        return UserModelOut(**user.to_dict())
    except UniqueViolationError:
        return status_code(
            400, return_error("Failed to create user. user already exists.")
        )


@docs(
    summary="This is an summary",
    description="This is an description of method",
    responses={200: "Returns a text saying OpenAPI Example"},
)
@app.router.get("/tasks/")
async def tasks() -> t.List[TaskModelOut]:
    q = await Task.select().order_by(Task.id)
    # queue.enqueue(print, q[0]['name'])
    # queue.enqueue(get_tasks)
    return q


@app.router.post("/tasks/")
async def create_task(task_model: FromJSON[TaskModelIn]) -> TaskModelOut:
    task = Task(**task_model.value.dict())
    await task.save()
    return TaskModelOut(**task.to_dict())


@app.router.put("/tasks/{task_id}/")
async def put_task(task_id: int, task_model: FromJSON[TaskModelIn]) -> TaskModelOut:
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return json({}, status=404)

    for key, value in task_model.value.dict().items():
        setattr(task, key, value)

    await task.save()

    return TaskModelOut(**task.to_dict())


@app.router.patch("/tasks/{task_id}/")
async def patch_task(
    task_id: int, task_model: FromJSON[TaskModelPartial]
) -> TaskModelOut:
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return json({}, status=404)

    for key, value in task_model.value.dict().items():
        if value is not None:
            setattr(task, key, value)

    await task.save()

    return TaskModelOut(**task.to_dict())


@app.router.delete("/tasks/{task_id}/")
async def delete_task(task_id: int):
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return json({}, status=404)

    await task.remove()

    return json({})


# Payments
@docs(
    summary="Creating link for payment",
    description="This is an description of method",
    responses={200: "Returns a text saying OpenAPI Example"},
    tags=["Billing & Payments"],
)
@app.router.post("/create_payment")
async def create_bill(user_id: int = 1, plan_id: int = 1):

    plan_query = await BillingPlans.objects().where(BillingPlans.id == plan_id).first()

    payment = Payment.create(
        {
            "amount": {"value": plan_query.amount, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": config.YOOMONEY_REDIRECT_URL,
            },
            "capture": True,
            "description": plan_query.description,
        },
        uuid.uuid4(),
    )

    # Return link for payment
    if payment.confirmation.confirmation_url:
        create_bill = await Bills.insert(
            Bills(
                uuid=payment.id,
                plan=plan_query.id,
                owner=user_id,
                amount=payment.amount.value,
            )
        )

        # Remove all unsuccessful payments by today
        # unsucessful_payments = await Bills.delete().where(
        #     Bills.in_progress == True,
        #     Bills.owner == user_id,
        # )

        return json(
            {
                "status": "success",
                "payment_id": payment.id,
                "url": payment.confirmation.confirmation_url,
            }
        )
    else:
        return json({"error": "Usucessful status response from payment gateway"})


@docs(
    summary="Payment info",
    description="This is an description of method",
    responses={200: "Returns a text saying OpenAPI Example"},
    tags=["Billing & Payments"],
)
@app.router.get("/payment/{payment_uuid}")
async def payment_page(payment_uuid: str) -> BillsModelOut:
    try:
        bill_query = await Bills.objects().where(Bills.uuid == payment_uuid).first()
        if bill_query and bill_query.payment_status not in ['payed', 'in_progress']:
             # Проверим синхронно, прошел ли платеж
            # Эта функция может работать лучше, например, через вебхуки кассы.
            payment = PaymentsHelper.get_payment_status(payment_uuid)
            match payment:
                case 'succeeded':
                    payment_status = await bill_query.update(
                        {
                            Bills.payed: True
                        }, force=True
                    ).where(Bills.uuid == payment_uuid)
                    payment_status = await Bills.select(Bills.plan.period.as_alias('period'), Bills.all_columns()).where(Bills.uuid == payment_uuid).first()
                    due = datetime.now() + timedelta(days=payment_status['period'])
                    profile = await BillingProfile.select(BillingProfile.id).where(BillingProfile.owner == payment_status['owner']).first()

                    create_subscription = await ActiveSubscriptions.insert(
                        ActiveSubscriptions(
                            owner=payment_status['owner'],
                            active_plan=payment_status['plan'],
                            billing_profile=profile['id'],
                            bill=payment_status['id'],
                            due_to=due
                        ))
                    return payment_status
                    # return BillsModelOut(**payment_status.to_dict())
        return BillsModelOut(**bill_query.to_dict())

    except AttributeError:
        return Response(404)


@docs(
    summary="Billing profile info",
    description="This is an description of method",
    responses={200: "Returns a text saying OpenAPI Example"},
    tags=["Billing & Payments"],
)
@app.router.get("/billing_profile/{user_id}")
async def profile_info(user_id: int) -> BillingProfileModelOut:
    user_info = (
        await BillingProfile.objects().where(BillingProfile.owner == user_id).first()
    )
    return BillingProfileModelOut(**user_info.to_dict())


# Payment hook
@app.router.get("/payment_hook")
async def payment_hook():
    pass


# Database connection pool
async def open_database_connection_pool(application):
    try:
        engine = engine_finder()
        await engine.start_connection_pool()
    except Exception:
        print("Unable to connect to the database")


async def close_database_connection_pool(application):
    try:
        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        print("Unable to connect to the database")


app.on_start += open_database_connection_pool
app.on_stop += close_database_connection_pool
