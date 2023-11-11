import pytest

from fastapi_htmx.htmx import _is_fullpage_request


class MockRequest:  # noqa: D101
    def __init__(self, headers: dict):  # noqa: D107
        self.headers = headers


@pytest.mark.parametrize(
    "headers,result",
    [
        ({"HX-Request": "true"}, False),
        ({"HX-Request": "TRUE"}, False),
        ({"HX-Request": "True"}, False),
        ({"HX-Request": "false"}, True),
        ({"HX-Request-Not": "true"}, True),
        ({}, True),
    ],
)
def test_is_fullpage_request(headers: dict, result: bool):
    request = MockRequest(headers=headers)

    assert _is_fullpage_request(request) == result  # Type: ignore
