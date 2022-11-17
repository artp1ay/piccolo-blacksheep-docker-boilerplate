import os

from blacksheep.contents import Content
from blacksheep.messages import Response
import jinja2


ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), "templates")
    )
)


async def home(request):
    template = ENVIRONMENT.get_template("home.html.jinja")
    content = template.render(
        title="Piccolo + ASGI",
    )
    return Response(
        200, content=Content(b"text/html", bytes(content, encoding="utf8"))
    )
