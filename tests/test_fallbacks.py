import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from fastapi_htmx import htmx, htmx_init


def test_async_no_response():
    app = FastAPI()
    htmx_init(templates=Jinja2Templates(directory=Path("tests") / "templates"))

    async def construct_root_page():
        await asyncio.sleep(0)
        return None

    @app.get("/", response_class=HTMLResponse)
    @htmx("index", "index")
    async def root_page(request: Request):
        return await construct_root_page()

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200


def test_async_redirect():
    app = FastAPI()
    htmx_init(templates=Jinja2Templates(directory=Path("tests") / "templates"))

    @app.get("/", response_class=HTMLResponse)
    @htmx("index", "index")
    def root_page(request: Request):
        return RedirectResponse("/target", status_code=302)

    @app.get("/target", response_class=HTMLResponse)
    @htmx("index", "index")
    def target_page(request: Request):
        return {"greeting": "redirected"}

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "redirected" in response.text
