from piccolo.table import Table
from piccolo.apps.user.tables import BaseUser
from piccolo.columns import (
    ForeignKey,
    Text,
    Varchar,
    Boolean,
    Float,
    UUID,
    Timestamp,
    Integer,
    LazyTableReference,
    OnDelete,
    JSONB,
)
from piccolo.columns.m2m import M2M
import datetime
from enum import Enum


class DefaultFields:
    updated_at = Timestamp(auto_update=datetime.datetime.now)
    created_at = Timestamp(default=datetime.datetime.now)


class BillingPlans(Table, DefaultFields, tablename="billing_plans", help_text="Тарифы"):
    """
    Тарифные планы
    """

    name = Varchar(length=255)
    description = Text(length=1024)
    amount = Float(default=0.0, required=True)
    continous = Boolean(default=False)
    is_active = Boolean(default=False)
    period = Integer(default=0)
    trial = Boolean(default=False)


class Bills(Table, DefaultFields, tablename="bills"):
    """
    Трнзакции. Каждая транзакция привязана к конкретному тарифному плану
    """

    class Status(str, Enum):
        expied = "expired"
        aborted = "aborted"
        holded = "holded"
        payed = "payed"
        in_progress = "in progress"

    uuid = UUID(unique=True)
    owner = ForeignKey(BaseUser)
    plan = ForeignKey(BillingPlans)
    amount = Float()
    in_progress = Boolean(default=True)
    holded = Boolean(default=False)
    expired = Boolean(default=False)
    aborted = Boolean(default=False)
    payed = Boolean(default=False)
    payment_data = JSONB(required=False)
    next_checkout = Timestamp(required=False)
    failed_attempts = Integer(default=0)
    last_failed_attempt = Timestamp(required=False)
    payment_status = Varchar(length=1, choices=Status, null=True)

    @classmethod
    def make_fail(self):
        self.aborted = True
        self.save()


class BillingProfile(
    Table,
    DefaultFields,
    tablename="billing_profiles",
    help_text="Платежные профили. Можель-расширение стандартной модели пользователя.",
):
    """
    Расширение модели User.
    Платежный профиль, хранит в себе данные о пользовательском профиле.
    Является расширением стандартной модели BaseUser.
    """

    uuid = UUID(unique=True)
    owner = ForeignKey(BaseUser)
    balance = Float(default=0.0)
    # active_plan = ForeignKey(BillingPlans, null=True)
    # active_bill = ForeignKey(Bills, null=True)
    # plan_end = Timestamp(null=True)
    # active = Boolean(default=False)


class ActiveSubscriptions(Table, DefaultFields, tablename="active_plans"):
    class Status(str, Enum):
        expied = "expired"
        aborted = "aborted"
        active = "active"
        blocked = "blocked"
        succeeded = "succeeded"

    owner = ForeignKey(BaseUser)
    active_plan = ForeignKey(BillingPlans)
    billing_profile = ForeignKey(BillingProfile)
    bill = ForeignKey(Bills)
    status = Varchar(length=1, choices=Status)
    due_to = Timestamp()
