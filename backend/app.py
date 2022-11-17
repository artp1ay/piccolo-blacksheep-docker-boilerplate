import sys

import typing as t

from piccolo_admin.endpoints import create_admin
from piccolo_admin.endpoints import TableConfig
from piccolo_api.crud.serializers import create_pydantic_model
from piccolo.engine import engine_finder

from blacksheep.server import Application
from blacksheep.server.bindings import FromJSON
from blacksheep.server.responses import json
from blacksheep.server.openapi.v3 import OpenAPIHandler
from openapidocs.v3 import Info

from home.endpoints import home
from home.piccolo_app import APP_CONFIG
from home.tables import Task
from billing.tables import BillingProfile, BillingPlans, Bills

# from q import queue
# from tasks import get_tasks

app = Application()

movie_config = TableConfig(BillingProfile, visible_columns=[BillingProfile.id, BillingProfile.profile_name])

app.mount(
    "/admin/",
    create_admin(
        [Task, BillingProfile, BillingPlans, Bills]
        # Required when running under HTTPS:
        # allowed_hosts=['my_site.com']
    ),
)

docs = OpenAPIHandler(info=Info(title="Saas Boilerplate API", version="0.0.1"))
docs.bind_app(app)


app.serve_files("static", root_path="/static")


app.router.add_get("/", home)

TaskModelIn: t.Any = create_pydantic_model(table=Task, model_name="TaskModelIn")
TaskModelOut: t.Any = create_pydantic_model(
    table=Task, include_default_columns=True, model_name="TaskModelOut"
)
TaskModelPartial: t.Any = create_pydantic_model(
    table=Task, model_name="TaskModelPartial", all_optional=True
)

@docs(
    summary="This is an summary",
    description="This is an description of method",
    responses={200: "Returns a text saying OpenAPI Example"}
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
async def put_task(
    task_id: int, task_model: FromJSON[TaskModelIn]
) -> TaskModelOut:
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
