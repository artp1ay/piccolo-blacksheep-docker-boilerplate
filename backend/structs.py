import typing as t
from piccolo_api.crud.serializers import create_pydantic_model
from piccolo.apps.user.tables import BaseUser
from billing.tables import BillingProfile, BillingPlans, Bills, ActiveSubscriptions


# User & Billing profile
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
    include_columns=(BaseUser.id, BaseUser.username, BaseUser.email, BaseUser.active),
)

# Payments
BillsModelOut: t.Any = create_pydantic_model(
    table=Bills,
    model_name="BillsModelOut",
    include_columns=(
        Bills.uuid,
        Bills.created_at,
        Bills.plan,
        Bills.amount,
        Bills.status,
    ),
)

# Subscriptions
ActiveSubscriptionsModelOut: t.Any = create_pydantic_model(
    table=ActiveSubscriptions,
    model_name="ActiveSubscriptionsModelOut",
    include_columns=(
        ActiveSubscriptions.id,
        ActiveSubscriptions.status,
        ActiveSubscriptions.due_to,
        ActiveSubscriptions.active_plan,
    ),
)
