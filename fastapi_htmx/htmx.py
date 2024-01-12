"""Extension for FastAPI to make HTMX easier to use."""
import inspect
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Dict, Optional, Union

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

TemplatePath = Union[Jinja2Templates, Dict[str, Jinja2Templates]]
TemplateName = str
templates_path: Optional[TemplatePath] = None
templates_file_extension: Optional[str] = None


@dataclass
class TemplateFileInfo:
    """A template collection and template name ready for use."""

    __slots__ = ("collection", "file_name")
    collection: Jinja2Templates
    file_name: TemplateName


@dataclass
class TemplateSpec:
    """A template specification in case multiple collections are used."""

    __slots__ = ("collection_name", "template_name")
    collection_name: str
    template_name: TemplateName


class MissingFullPageTemplateError(HTTPException):
    """Fullpage request not a corresponding template configured for url rewriting and history to work."""

    def __init__(self) -> None:  # noqa: D107
        super().__init__(status_code=400, detail="Ressource cannot be accessed directly.")
        logging.debug(
            "Route is not configured to be queried directly. Please specify a fullpage template + data for that."
        )


class MissingHTMXInitError(Exception):
    """FastAPI-HTMX was not initialized."""

    pass


class InvalidHTMXInitError(Exception):
    """FastAPI-HTMX was not initialized properly."""

    pass


class HXRequest(Request):
    """FastAPI Request Object with HTMX additions."""

    hx_request: bool = False


def _get_template_name(name: Union[TemplateSpec, str], file_extension: Optional[str]) -> TemplateFileInfo:
    if isinstance(name, TemplateSpec) and isinstance(templates_path, dict):
        try:
            templates_collection_path = templates_path[name.collection_name]
            template_name_in_collection = name.template_name
        except KeyError:
            raise InvalidHTMXInitError(
                "FASTAPI-HTMX was not initialized properly."
                "Please specify all collections of templates used in the decorators"
            )
    else:
        templates_collection_path = templates_path  # type: ignore
        template_name_in_collection = name  # type: ignore

    if file_extension is None:
        file_extension = templates_file_extension

    template_file_name_in_collection = f"{template_name_in_collection}.{file_extension}"

    return TemplateFileInfo(collection=templates_collection_path, file_name=template_file_name_in_collection)


def htmx(  # noqa: C901
    partial_template_name: Union[TemplateSpec, TemplateName],
    full_template_name: Optional[Union[TemplateSpec, TemplateName]] = None,
    partial_template_constructor: Optional[Callable] = None,
    full_template_constructor: Optional[Callable] = None,
    template_extension: Optional[str] = None,
) -> Callable:
    """Decorator for FastAPI routes to make HTMX easier to use.

    Args:
        partial_template_name (Union[TemplateSpec, TemplateName]): A Template for the partial to use.
        full_template_name (Optional[Union[TemplateSpec, TemplateName]]): The full page template name.
                                                                                        Defaults to None.
        partial_template_constructor (Optional[Callable]): A Callable returning the needed variables for the template.
                                                           Defaults to None.
        full_template_constructor (Optional[Callable]): A Callable returning the needed variables for the template.
                                                        Defaults to None.
        template_extension (Optional[str]): The template extension to use. Defaults to None.

    Raises:
        MissingFullPageTemplateError: If a full page is required bu no template is specified.
        MissingHTMXInitError: FastAPI-HTMX needs to be initialized for templates to work.

    Returns:
        Callable: The decorated function.
    """  # noqa: D401

    def htmx_decorator(func):  # noqa: C901
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs) -> Callable:  # noqa: C901
            request_is_fullpage_request = _is_fullpage_request(request=request)
            # hint: use `HXRequest` instead of `Request` for typing when using `request.hx_request`
            request.hx_request = not request_is_fullpage_request  # type: ignore

            # convenient history support if kwargs match in the endpoint and constructor
            if request_is_fullpage_request and full_template_constructor is not None:
                if inspect.iscoroutinefunction(full_template_constructor):
                    response = await full_template_constructor(**kwargs)
                else:
                    response = full_template_constructor(**kwargs)
            elif not request_is_fullpage_request and partial_template_constructor is not None:
                if inspect.iscoroutinefunction(partial_template_constructor):
                    response = await partial_template_constructor(**kwargs)
                else:
                    response = partial_template_constructor(**kwargs)
            else:
                if inspect.iscoroutinefunction(func):
                    response = await func(*args, request=request, **kwargs)
                else:
                    response = func(*args, request=request, **kwargs)

            # in case no constructor function or return dict was supplied, assume a template not needing variables
            if response is None:
                logging.debug("No data provided for endpoint, providing an empty dict.")
                response = {}

            # in case of RedirectResponse or similar
            if not isinstance(response, Mapping):
                return response

            template_name = partial_template_name
            if request_is_fullpage_request:
                if full_template_name is None:
                    raise MissingFullPageTemplateError()
                template_name = full_template_name

            if templates_path is None:
                raise MissingHTMXInitError(
                    "FASTAPI-HTMX was not initialized properly. "
                    "Please call 'htmx_init(Jinja2Templates(directory=Path('templates')))' in your app "
                    "before using the '@htmx(...)' decorator"
                )

            template = _get_template_name(name=template_name, file_extension=template_extension)
            return template.collection.TemplateResponse(
                template.file_name,
                {
                    "request": request,
                    **response,
                },
            )

        return wrapper

    return htmx_decorator


def _is_fullpage_request(request: Request) -> bool:
    return "HX-Request" not in request.headers or request.headers["HX-Request"].lower() != "true"


def htmx_init(templates: TemplatePath, file_extension: str = "jinja2"):
    """Initialize the HTMX extension.

    Args:
        templates (TemplatePath): The configured template instance to use.
                                  Or multiple template collections distinguished by a key.
        file_extension: (str): The file extension to use for all templates. Can be individually overriden.
    """
    global templates_path
    templates_path = templates
    global templates_file_extension
    templates_file_extension = file_extension
