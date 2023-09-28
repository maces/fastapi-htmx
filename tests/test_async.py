import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from fastapi_htmx import htmx, htmx_init


def test_async_partial_constructors():
    app = FastAPI()
    htmx_init(templates=Jinja2Templates(directory=Path("tests") / "templates"))

    async def construct_customers():
        await asyncio.sleep(0)
        return {"customers": ["John Doe", "Jane Doe"]}

    async def construct_root_page():
        await asyncio.sleep(0)
        return {"greeting": "Hello World", **await construct_customers()}

    @app.get("/", response_class=HTMLResponse)
    @htmx("index", "index")
    async def root_page(request: Request):
        return await construct_root_page()

    @app.get("/customers", response_class=HTMLResponse)
    @htmx("customers", "index", construct_customers, construct_root_page)
    async def get_customers(request: Request):
        pass

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>Hello World</h1>" in response.text
    assert "<li>John Doe</li>" in response.text
    assert "<li>Jane Doe</li>" in response.text

    response = client.get("/customers")
    assert response.status_code == 200
    assert "<h1>Hello World</h1>" in response.text
    assert "<li>John Doe</li>" in response.text
    assert "<li>Jane Doe</li>" in response.text

    # check if a partial does not include the root page
    response = client.get("/customers", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<h1>Hello World</h1>" not in response.text
    assert "<li>John Doe</li>" in response.text
    assert "<li>Jane Doe</li>" in response.text
