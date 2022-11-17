import os

from piccolo.engine.postgres import PostgresEngine
import config

from piccolo.conf.apps import AppRegistry

DB = PostgresEngine(
    config={
        "database": config.PG_DATABASE,
        "user": config.PG_USER,
        "password": config.PG_PASSWORD,
        "host": os.environ.get("PG_HOST", config.PG_HOST),
        "port": int(os.environ.get("PG_PORT", config.PG_PORT)),
    }
)

APP_REGISTRY = AppRegistry(
    apps=["home.piccolo_app", "piccolo_admin.piccolo_app", "billing.piccolo_app"]
)

# APPS = [f"{name}.piccolo_app" for name in os.listdir(".") if os.path.isdir(name) and "_" not in name]
#
# APP_REGISTRY = AppRegistry(apps=APPS)
