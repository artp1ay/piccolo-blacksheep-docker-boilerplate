import requests
import config
import yookassa
from yookassa import Configuration, Payment
from billing.tables import BillingProfile, BillingPlans, Bills


# Yookassa
Configuration.account_id = config.YOOKASSA_ACCOUNT_ID
Configuration.secret_key = config.YOOKASSA_SECRET_KEY


class PaymentsHelper:
    @staticmethod
    def get_payment_status(payment_id: str) -> str:
        return Payment.find_one(str(payment_id)).status

    @staticmethod
    def cancel_payment(payment_id: str) -> Payment:
        return Payment.cancel(str(payment_id))


class SubscriptionHelper:
    @staticmethod
    async def check_subscription(user_id: int) -> bool:
        return await BillingProfile.objects().where(BillingProfile.owner == user_id)


def return_error(details: str) -> dict:
    return {"error": True, "details": details}


