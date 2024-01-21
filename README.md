# FastAPI-HTMX

Extension for FastAPI to make HTMX easier to use.

FastAPI-HTMX is an opinionated extension for FastAPI to speed up development of lightly interactive web applications. FastAPI-HTMX is implemented as a decorator, so it can be used on endpoints selectively. Furthermore it reduces boilerplate for Jinja2 template handling and allows for rapid prototyping by providing convenient helpers.

[![Tests](https://github.com/maces/fastapi-htmx/actions/workflows/github-actions-tests.yml/badge.svg)](https://github.com/maces/fastapi-htmx/actions/workflows/github-actions-tests.yml)
[![Version](https://img.shields.io/pypi/v/fastapi-htmx?logo=pypi&logoColor=white&color=2ab049)](https://pypi.org/project/fastapi-htmx/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-htmx.svg?color=2ab049)](https://pypi.org/project/fastapi-htmx/)
[![Experimental Support Chat](https://img.shields.io/badge/ChatGPT-Experimental_Support_Chat-white?logo=chatbot&color=2ab049)](https://chat.openai.com/g/g-FdDQll0CW-fastapihtmx)


## Install

install via `pip`:
```
$ pip install fastapi-htmx
```

install via `poetry`:
```
$ poetry add fastapi-htmx
```


## Usage

### Getting Started

Basic example using FastAPI with `fastapi-htmx`

`my_app/api.py`:
```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx, htmx_init

app = FastAPI()
htmx_init(templates=Jinja2Templates(directory=Path("my_app") / "templates"))

@app.get("/", response_class=HTMLResponse)
@htmx("index", "index")
async def root_page(request: Request):
    return {"greeting": "Hello World"}

@app.get("/customers", response_class=HTMLResponse)
@htmx("customers")
async def get_customers(request: Request):
    return {"customers": ["John Doe", "Jane Doe"]}
```

Note that:
- `htmx()` got parameters, specifying the Jinja2 template to use
- `htmx_init()` is needed for FastAPI-HTMX to find the templates
- **There is no direct handling of the template needed, it only needs to be specified and the needed variables need to be returned**. This way endpoints can be designed in a familiar way to standard REST endpoints in FastAPI.
    - This simplifies modularizing the app later (see below) and also providing a REST API if needed. See the "Usage" section for further examples.
    - `get_customers` does not respond with the whole web page, but only with a part of it. See the [HTMX documentation](https://htmx.org/docs/#introduction) on how HTMX merges partials into the current web page.
- **`request: Request` although not used in the endpoint directly, it is currently required for the decorator to work!**

The [Jinja2 templates](https://jinja.palletsprojects.com/en/3.1.x/templates/) to go along with the above code need to be placed like specified in `htmx_init` in `my_app/templates/` in order for the example to work.

The root page `my_app/templates/index.jinja2`:
```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>Hello FastAPI-HTMX</title>
</head>
<body>
    <h1>{{ greeting }}</h1>
    <button
        hx-get="/customers"
        hx-swap="innerHTML"
        hx-target="#customers_list"
    >
        Load Data
    </button>
    <div id="customers_list"></div>
    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
</body>
</html>
```

The [partial template to load with HTMX](https://htmx.org/docs/#introduction) `my_app/templates/customers.jinja2`:
```jinja2
<ul>
    {% for customer in customers %}
        <li>{{ customer }}</li>
    {% endfor %}
</ul>
```


### Main Concept

The decorator `htmx` provides the following helpers:

- `partial_template_name` The partial template to use
- `full_template_name` The full page template to use when URL rewriting + history is used
- `*_template_constructor` For DRY code, in case the logic to gather all needed variables is needed multiple times

Seeing these arguments one might ask themselves: Why all these parameters? The answer is an opinionated take on how to design modular endpoints wit partials and url-rewriting support:

The idea behind FastAPI-HTMX is to maintain a modular structure in the app and with the endpoints. Similar to a REST API with a [SPA](https://developer.mozilla.org/en-US/docs/Glossary/SPA). This way the frontend can be modular as well. This majorly helps with supporting [URL rewriting and the history](https://htmx.org/docs/#history) in the frontend:

- A simple endpoint just answers with the partial.
- Without it, if the URL is rewritten and a user navigates back, reloads the page or copies the URL and opens it in another tab or shares the URL, only the partial would be shown in the browser.

**To enable SPA like functionality FastAPI-HTMX uses the concept of partials and fullpages as arguments for the decorator and requires to return a dict of the needed variables**. Note that returning anything else than a `Mapping` like a dict in the route, leads FastAPI-HTMX to return that instead of a template.

In order to support this SPA like functionality in an app, see the following example:

`my_app/api_with_constructors.py`:
```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx, htmx_init

app = FastAPI()
htmx_init(templates=Jinja2Templates(directory=Path("my_app") / "templates"))

def construct_customers():
    return {"customers": ["John Doe", "Jane Doe"]}

def construct_root_page():
    return {
        "greeting": "Hello World",
        **construct_customers()
    }

@app.get("/", response_class=HTMLResponse)
@htmx("index", "index")
async def root_page(request: Request):
    return construct_root_page()

@app.get("/customers", response_class=HTMLResponse)
@htmx("customers", "index", construct_customers, construct_root_page)
async def get_customers(request: Request):
    pass
```

Note that:
- The `construct_*` functions are added, they now return the data
    - **`construct_root_page` gathers all variables specified needed for the root page, including those for partials**
        - **This also means you must avoid naming conflicts across endpoints, so dicts can be merged.**
        - Costly operations can still be ignored, just use if statements in the template or similar
- The decorators arguments are extended
    - The second argument is the fullpage template which is used when the endpoint is called directly (new tab, navigation or reload)
        - **E.g. since `construct_root_page` gathers all the data for the whole page, the whole page can be returned to the client**
    - The other arguments are just to save some boilerplate code handling the [`HX-Request` header](https://htmx.org/attributes/hx-push-url/)
        - **There is no need to use the arguments for the constructor functions, they are just for convenience.** If needed the endpoint can be used for the logic as well. Especially if no URL rewriting is needed.

For the above code to work the `my_app/templates/index.jinja2` needs to be changed as well. The changes are in the button and target div.
Changed root page `my_app/templates/index.jinja2`:
```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>Hello FastAPI-HTMX</title>
</head>
<body>
    <h1>{{ greeting }}</h1>
    <button
        hx-get="/customers"
        hx-push-url="true"
        hx-swap="innerHTML"
        hx-target="#customers_list"
    >
        Load Data
    </button>
    <div id="customers_list">
        {% include 'customers.jinja2' %}
    </div>
    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
</body>
</html>
```

Note that:
- `hx-push-url="true"` was added to the button
- The partial is now loaded by default requiring the main endpoint to also provide the needed variables like shown above

The unchanged partial `my_app/templates/customers.jinja2`:
```jinja2
<ul>
    {% for customer in customers %}
        <li>{{ customer }}</li>
    {% endfor %}
</ul>
```

To add additional partials and endpoints just repeat the same logic:
- Include the partial in the parent Jinja2 template, like the main template. A hierarchy is possible as well.
- Refactor the partials endpoints logic into a function
    - Add it's return value to the parents constructor function like done above in `construct_root_page`
    - Add the parents template and constructor function to the partials endpoints `htmx` decorator arguments


### Advanced Usage


#### Handling `HX-Request` manually

In case the `htmx()` arguments for partial and fullpage callables are not flexible enough, an endpoint can be used like usual. For a bit more convenience the `HX-Request` header is easily accessible via `request.hx_request`:

`my_app/api_with_hx_request.py`:
```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_htmx import HXRequest, htmx, htmx_init

app = FastAPI()
htmx_init(templates=Jinja2Templates(directory=Path("my_app") / "templates"))

def my_partial(email_id: int = None):
    return {"email_id": email_id}

def fullpage(email_id: int = None):
    return {**my_partial(email_id)}

@app.get("/email/{email_id}", response_class=HTMLResponse)
@htmx("email_detail", "index")
def get_email(request: HXRequest, email_id: int):
    if request.hx_request:
        return my_partial(email_id)
    else:
        return fullpage(email_id)
```

`my_app/templates/index.jinja2`:
```jinja2
<!DOCTYPE html>
<html><head><title>Hello FastAPI-HTMX</title></head>
<body>
    <div id="email_detail">
        {% include 'email_detail.jinja2' %}
    </div>
    <script src="https://unpkg.com/htmx.org@1.9.6"></script>
</body>
</html>
```

`my_app/templates/email_detail.jinja2`:
```jinja2
<p>{{ email_id }}</p>
```


#### Filters

In order to use [custom Jinja2 filters](https://jinja.palletsprojects.com/en/3.1.x/api/#custom-filters) like the following, configure them like below.

`my_app/templates/customer.jinja2`:
```Jinja2
<p>{{ customer.created|datetime_format }}</p>
```

Add custom filters for use in Jinja2 templates:
`my_app/api_template_filters.py`:
```python
from pathlib import Path
from datetime import datetime

from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx_init

def datetime_format(value: datetime, format="%H:%M %d.%m.%Y"):
    return value.strftime(format) if value is not None else ""

templates = Jinja2Templates(directory=Path("my_app") / "templates")
templates.env.filters["datetime_format"] = datetime_format
htmx_init(templates=templates)
# ...
```


#### Multiple Template Directories

For bigger apps, multiple template directories might be needed. For example if the app is split into several modules connected with routers. For this case template collections can be used. With `htmx_init()` multiple template collections can be defined. In each endpoint instead of the templates name (`account`) the collection gets specified as well, like this: `Tpl(SHOP, "account")`. This works for partials and full pages.

`my_app/api_multiple_template_paths.py`:
```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx, htmx_init, TemplateSpec as Tpl

SHOP = "shop"
BACKEND = "backend"

app = FastAPI()
templates = {
    SHOP: Jinja2Templates(directory=Path("my_app") / SHOP / "templates"),
    BACKEND: Jinja2Templates(directory=Path("my_app") / BACKEND / "templates")
}
htmx_init(templates=templates)

@app.get("/account", response_class=HTMLResponse)
@htmx(Tpl(SHOP, "account"))
async def get_account(request: Request):
    pass

@app.get("/products", response_class=HTMLResponse)
@htmx(Tpl(BACKEND, "products"))
async def get_products(request: Request):
    pass

```

`my_app/shop/templates/account.jinja2`:
```jinja2
<h1>My Account</h1>
```

`my_app/backend/templates/products.jinja2`:
```jinja2
<h1>Products</h1>
```


#### Other template file extensions for SOME endpoints

In case SOME endpoints templates got another file extension than the rest, it can be specified in the `@htmx()` decorator:

`my_app/api_template_file_extension.py`:
```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx, htmx_init

app = FastAPI()
htmx_init(templates=Jinja2Templates(directory=Path("my_app") / "templates"))

@app.get("/customers", response_class=HTMLResponse)
@htmx("customers", template_extension="html")
async def get_customers(request: Request):
    pass
# ...
```

`my_app/templates/customers.html`:
```jinja2
<h1>Customer</h1>
```


#### Other template file extensions for ALL endpoints

In case ALL endpoints templates got another file extension than the default `jinja2`, it can be overriden in `htmx_init()` like this:

`my_app/api_template_file_extension.py`:
```python
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx, htmx_init

app = FastAPI()
templates = Jinja2Templates(directory=Path("my_app") / "templates")
htmx_init(templates=templates, file_extension="html")

@app.get("/customers", response_class=HTMLResponse)
@htmx("customers")
async def get_customers(request: Request):
    pass
```

`my_app/templates/customers.html`:
```jinja2
<h1>Customer</h1>
```
