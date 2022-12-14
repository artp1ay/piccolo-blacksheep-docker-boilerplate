from piccolo.table import Table
from piccolo.apps.user.tables import BaseUser
from piccolo.columns import ForeignKey, Text, Varchar, Boolean, Float, UUID, Timestamp, Integer, LazyTableReference, OnDelete
from piccolo.columns.m2m import M2M
import datetime


class BillingPlans(Table, tablename="billing_plans", help_text="Тарифы"):
	"""
	Тарифные планы
	"""
	name = Varchar(length=255)
	description = Text(length=1024)
	amount = Float(default=0.0, required=True)
	continous = Boolean(default=False)
	is_active = Boolean(default=False)
	period = Integer(default=0)
	updated_at = Timestamp(auto_update=datetime.datetime.now)
	created_at = Timestamp(default=datetime.datetime.now)


class Bills(Table, tablename="bills"):
	"""
	Трнзакции. Каждая транзакция привязана к конкретному тарифному плану
	"""
	uuid = UUID(unique=True)
	owner = ForeignKey(BaseUser)
	plan = ForeignKey(BillingPlans)
	amount = Float()
	in_progress = Boolean(default=True)
	holded = Boolean(default=False)
	expired = Boolean(default=False)
	aborted = Boolean(default=False)
	updated_at = Timestamp(auto_update=datetime.datetime.now)
	created_at = Timestamp(default=datetime.datetime.now)

	@classmethod
	def make_fail(self):
		self.aborted = True
		self.save()


class BillingProfile(Table, tablename="billing_profiles", help_text="Платежные профили. Можель-расширение стандартной модели пользователя."):
	"""
	Расширение модели User.
	Платежный профиль, хранит в себе данные о текущем тарифе.
	"""
	uuid = UUID(unique=True)
	owner = ForeignKey(BaseUser)
	balance = Float(default=0.0)
	profile_name = Varchar(length=255)
	active_plan = ForeignKey(BillingPlans, null=True)
	active_bill = ForeignKey(Bills, null=True)
	plan_end = Timestamp(null=True)
	active = Boolean(default=False)
	updated_at = Timestamp(auto_update=datetime.datetime.now)
	created_at = Timestamp(default=datetime.datetime.now)




