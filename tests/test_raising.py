import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

from fastapi_htmx import htmx, htmx_init
from fastapi_htmx.htmx import MissingFullPageTemplateError


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

    with pytest.raises(MissingFullPageTemplateError):
        client.get("/")
