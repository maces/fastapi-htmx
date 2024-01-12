import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from fastapi_htmx import TemplateSpec as Tpl
from fastapi_htmx import htmx, htmx_init
from fastapi_htmx.htmx import InvalidHTMXInitError, MissingHTMXInitError


def test_missing_request():
    app = FastAPI()
    htmx_init(templates=Jinja2Templates(directory=Path("tests") / "templates"))

    @app.get("/", response_class=HTMLResponse)
    @htmx("index", "index")
    async def root_page():  # missing request
        await asyncio.sleep(0)
        return {"greeting": "Hello World", "customers": ["John Doe", "Jane Doe"]}

    client = TestClient(app)

    with pytest.raises(TypeError):
        client.get("/")


def test_missing_fullpage_template():
    app = FastAPI()
    htmx_init(templates=Jinja2Templates(directory=Path("tests") / "templates"))

    @app.get("/", response_class=HTMLResponse)
    @htmx("index")  # missing fullpage template
    async def root_page(request: Request):
        await asyncio.sleep(0)
        return {}

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 400


def test_missing_init():
    app = FastAPI()
    htmx_init(None)  # type: ignore

    @app.get("/", response_class=HTMLResponse)
    @htmx("index", "index")
    async def root_page(request: Request):
        await asyncio.sleep(0)
        return {}

    client = TestClient(app)

    with pytest.raises(MissingHTMXInitError):
        client.get("/")


def test_template_collection_not_found():
    app = FastAPI()
    htmx_init(templates={"wrong": Jinja2Templates(directory=Path("my_app") / "wrong" / "templates")})

    @app.get("/", response_class=HTMLResponse)
    @htmx(Tpl("correct", "index"), Tpl("correct", "index"))
    async def root_page(request: Request):
        await asyncio.sleep(0)
        return {}

    client = TestClient(app)

    with pytest.raises(InvalidHTMXInitError):
        client.get("/")
