import requests
import config
import yookassa
from yookassa import Configuration, Payment
from billing.tables import BillingProfile, BillingPlans, Bills, ActiveSubscriptions


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
        """
        Checks if user have an active subscription.
        return: bool
        """
        active_subscription = await ActiveSubscriptions.select().where((ActiveSubscriptions.owner == user_id) & (ActiveSubscriptions.status == ActiveSubscriptions.Status.active))
        return bool(active_subscription)


def return_error(details: str) -> dict:
    """
    Text placeholder for error fallback in response
    return: dict
    """
    return {"error": True, "details": details}


