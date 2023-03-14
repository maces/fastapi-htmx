# FastAPI-HTMX

Extension for FastAPI to make HTMX easier to use.

FastAPI-HTMX is implemented as a decorator, so it can be used selectively on routes in you FastAPI project. Furthermore it reduces boilerplate and allows for rapid prototyping by providing convenient helpers.

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
- `htmx()` got a parameter, which is the Jinja2 template to use
- `htmx_init()` is needed for FastAPI-HTMX to find the templates and more
- **There is no direct usage of a template, instead the template is specified and the needed variables are passed on by returning them**. Similar to a standard REST endpoint.
    - This simplifies switching between templates and REST endpoints. See the "Usage" section for further examples.
- **`request: Request` although not used, it is currently required for the decorator to work!**

The above example also needs these very basic [Jinja2 templates](https://jinja.palletsprojects.com/en/3.1.x/templates/) in `my_app/templates/` to work.

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
    <script src="https://unpkg.com/htmx.org@1.8.6"></script>
</body>
</html>
```

The [partial template to load with htmx](https://htmx.org/docs/#introduction) `my_app/templates/customers.jinja2`:
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

Seeing these arguments one might ask themselves: Why use a full template or functions to provide the variables for the templates if there is an endpoint anyway?

The idea behind FastAPI-HTMX is to maintain a modular structure in the app and with the endpoints. Similar to a REST API with a [SPA](https://developer.mozilla.org/en-US/docs/Glossary/SPA). This way the frontend can be modular as well. This majorly helps with supporting [URL rewriting and the history](https://htmx.org/docs/#history) in the frontend. A simple endpoint just answers with the partial. If the URL is rewritten and a user navigates back, reloads the page or copies the URL and opens it in another tab or shares it, only the partial would be shown in the browser. **To enable this SPA like functionality FastAPI-HTMX provides these arguments for the decorator and requires to return a dict of the needed variables**. In order to support this in an app, see the following example:

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
- The `construct_*` functions where added, they now return the data
    - **`construct_root_page` gathers all variables specified needed for the root page, including partials**
        - **This also means you must avoid naming conflicts across endpoints.**
        - Costly operations can still be ignored, just use if statements in the template or similar
- The decorators arguments where extended
    - The second argument is the template to use when the rewritten URL is used directly (new tab, navigation or reload)
        - **Since `construct_root_page` gathers all the data for the whole page, the whole page can be returned to the client**
    - The other arguments are just to save some boilerplate code handling the [`HX-Request` header](https://htmx.org/attributes/hx-push-url/)
        - **There is no need to use these arguments of the decorator, they are just for convenience.** If needed the endpoint can be used for the logic as well. Especially if no URL rewriting is needed.

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
    <script src="https://unpkg.com/htmx.org@1.8.6"></script>
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

Additional partials and their endpoints can be added by the same logic:
- Include the partial in the parent Jinja2 template, like the main template. A hierarchy is possible as well.
- Refactor the partials endpoints logic into a function
    - Add it's return vale to the parents constructor function like above
    - Add the parents template and constructor function to the partials endpoints htmx decorator arguments

### Advanced Usage

Add [custom filters](https://jinja.palletsprojects.com/en/3.1.x/api/#custom-filters) to Jinja2 templates:
```python
# ...
def datetime_format(value: datetime, format="%H:%M %d.%m.%Y"):
    return value.strftime(format) if value is not None else ""

templates = Jinja2Templates(directory=Path("my_app") / "templates")
templates.env.filters["datetime_format"] = datetime_format
htmx_init(templates=templates)
# ...
```
