import sys
from subprocess import call
import uuid
import config
import typing as t

from piccolo_admin.endpoints import create_admin
from piccolo_admin.endpoints import TableConfig
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
from billing.tables import BillingProfile, BillingPlans, Bills, ActiveSubscriptions
from structs import (
    BillingProfileModelOut,
    UserModelIn,
    UserModelOut,
    BillsModelOut,
    ActiveSubscriptionsModelOut,
)

from yookassa import Configuration, Payment
from datetime import datetime, timedelta
from helpers import PaymentsHelper, SubscriptionHelper, return_error
from asyncpg.exceptions import UniqueViolationError
from mailer.events import register_user


# Yookassa
Configuration.account_id = config.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY

app = Application(show_error_details=False)

movie_config = TableConfig(BillingProfile, visible_columns=[BillingProfile.id])

app.mount(
    "/admin/",
    create_admin(
        [BillingProfile, BillingPlans, Bills, ActiveSubscriptions]
        # Required when running under HTTPS:
        # allowed_hosts=['my_site.com']
    ),
)

docs = OpenAPIHandler(info=Info(title="Saas Boilerplate API", version="0.0.1"))
docs.bind_app(app)


# Task Handlers
# Hooks for starting and stopping RQ jobs
@app.after_start
async def after_start(application: Application) -> None:
    from executor import periodic_tasks


@app.on_stop
async def on_stop(application: Application) -> None:
    from executor import regular_queue, periodic_queue

    for job in regular_queue:
        job.empty()
    for job in periodic_queue:
        job.empty()


@docs(
    summary="Create user with billing profile",
    responses={200: "User created", 400: "User already exists"},
    tags=["Users & Auth"],
)
@app.router.post("/create_user")
async def create_user(user_data: FromJSON[UserModelIn]) -> UserModelOut:
    try:
        user = await BaseUser.create_user(**user_data.value.dict(), active=True)
        billing_profile = BillingProfile(owner=user.id)
        if user:
            await billing_profile.save()

            # Sending Email
            user_data = user.to_dict()
            register_user(email_to=user_data['email'], username=user_data['username'])

        return UserModelOut(**user.to_dict())
    except UniqueViolationError:
        return status_code(
            400, return_error("Failed to create user. user already exists.")
        )


# Payments
@docs(
    summary="Creating link for payment",
    description="Creates a link to make a payment in the YooKassa service if the user does not have an active subscription. ",
    responses={
        200: "Sucessfuly created payment",
        408: "Usucessful status response from payment gateway",
        406: "User already have an active subscription",
    },
    tags=["Billing & Payments"],
)
@app.router.put("/create_payment")
async def create_bill(user_id: int = 1, plan_id: int = 1):

    # Check if the user has an active subscription
    # If there is an active subscription, we return the error response
    if await SubscriptionHelper.check_subscription(user_id):
        return status_code(
            400, return_error(f"User alredy have an active subscription.")
        )

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

        return json(
            {
                "status": "success",
                "payment_id": payment.id,
                "url": payment.confirmation.confirmation_url,
            }
        )
    else:
        return status_code(
            408, return_error(f"Usucessful status response from payment gateway")
        )


@docs(
    summary="Subscription info",
    responses={
        200: "Returns active user subscription",
    },
    tags=["Subscriptions"],
)
@app.router.get("/subscription/{user_id}")
async def get_subscription(user_id: int) -> ActiveSubscriptionsModelOut:
    subscription = (
        await ActiveSubscriptions.select()
        .where(
            (ActiveSubscriptions.owner == user_id)
            & (ActiveSubscriptions.status == ActiveSubscriptions.Status.active)
        )
        .order_by(ActiveSubscriptions.due_to, ascending=False)
        .first()
    )
    if subscription:
        return ActiveSubscriptionsModelOut(**subscription)
    else:
        return {"response": "no subscription"}


@docs(summary="List of all subscriptions", tags=["Subscriptions"])
@app.router.get("/subscriptions_list/{user_id}")
async def subscriptions_list(user_id: int) -> t.List[ActiveSubscriptionsModelOut]:
    subscriptions = (
        await ActiveSubscriptions.select()
        .where(ActiveSubscriptions.owner == user_id)
        .order_by(ActiveSubscriptions.status)
    )
    return [ActiveSubscriptionsModelOut(**sub) for sub in subscriptions]


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
        if bill_query and bill_query.status not in [
            Bills.Status.paid,
            Bills.Status.in_progress,
        ]:

            # Check in sync if the payment was successful
            # This feature may work better, for example, through the webhooks of the yookassa
            payment = PaymentsHelper.get_payment_status(payment_uuid)
            print(payment)
            match payment:
                case "succeeded":
                    payment_status = await bill_query.update(
                        {
                            Bills.status: Bills.Status.paid,
                        },
                        force=True,
                    ).where(Bills.uuid == payment_uuid)
                    payment_status = (
                        await Bills.select(
                            Bills.plan.period.as_alias("period"), Bills.all_columns()
                        )
                        .where(Bills.uuid == payment_uuid)
                        .first()
                    )
                    due = datetime.now() + timedelta(days=payment_status["period"])
                    profile = (
                        await BillingProfile.select(BillingProfile.id)
                        .where(BillingProfile.owner == payment_status["owner"])
                        .first()
                    )

                    # Checking if active subscription not exists, if not then create
                    if not await ActiveSubscriptions.select(
                        ActiveSubscriptions.all_columns(), ActiveSubscriptions.bill.uuid
                    ).where(
                        (ActiveSubscriptions.bill.uuid == payment_uuid)
                        & (
                            ActiveSubscriptions.status
                            == ActiveSubscriptions.Status.active
                        )
                    ):
                        create_subscription = await ActiveSubscriptions.insert(
                            ActiveSubscriptions(
                                owner=payment_status["owner"],
                                active_plan=payment_status["plan"],
                                billing_profile=profile["id"],
                                bill=payment_status["id"],
                                status=ActiveSubscriptions.Status.active,
                                due_to=due,
                            )
                        )
                    return BillsModelOut(**payment_status)

                case "pending":
                    if bill_query.status != Bills.Status.pending:
                        bill_query = (
                            await Bills.update({Bills.status: Bills.Status.pending})
                            .where(Bills.uuid == payment_uuid)
                            .returning(
                                Bills.created_at, Bills.plan, Bills.amount, Bills.status
                            )
                        )
                        return BillsModelOut(**bill_query[0])

                    # raise ValueError("This is an error of create_subscription")
                    # return BillsModelOut(**payment_status.to_dict())
        return BillsModelOut(**bill_query.to_dict())

    except AttributeError:
        return status_code(404, return_error("Payment not found"))


@docs(
    summary="Cancel payment by its UUID",
    responses={
        200: "Successful cancel payment by its UUID",
        403: "Payment have not match requirement status and cannot be cacnelled.",
        404: "Payment not found",
    },
    tags=["Billing & Payments"],
)
@app.router.delete("/cancel_payment/{payment_uuid}")
async def cancel_payment(payment_uuid: str) -> BillsModelOut:
    try:
        payment = await Bills.objects().where(Bills.uuid == payment_uuid).first()
        if not payment.status or payment.status not in (
            Bills.Status.paid,
            Bills.Status.cancelled,
        ):
            print(payment)
            payment = (
                await Bills.update({Bills.status: Bills.Status.cancelled})
                .where(Bills.uuid == payment_uuid)
                .returning(Bills.created_at, Bills.plan, Bills.amount, Bills.status)
            )
            print(payment)
            return BillsModelOut(**payment[0])
        else:
            return status_code(
                403,
                return_error(
                    "Payment have not match requirement status and cannot be cacnelled."
                ),
            )
    except AttributeError as e:
        print(e)
        return status_code(404, return_error("Payment not found"))


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
@app.router.get("/test")
async def test_endpoint():
    req = await ActiveSubscriptions.select(
        ActiveSubscriptions.all_columns(), ActiveSubscriptions.bill.uuid
    ).where(
        (ActiveSubscriptions.bill.uuid == "2b0ee4ab-000f-5000-9000-1fa2b67816e9")
        & (ActiveSubscriptions.status == ActiveSubscriptions.Status.active)
    )
    print(req)
    return {"status": "done"}


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
