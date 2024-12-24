import re
import shutil
import textwrap
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

file_name_in_markdown_pattern = re.compile("`([a-zA-Z0-9/_.]*)`")


def extract_test_cases_from_readme() -> dict[str, dict[str, str]]:
    print(Path(".").absolute())
    test_cases: dict[str, dict[str, str]] = {}
    with open(Path("README.md")) as readme_file:
        readme = textwrap.dedent(readme_file.read())
        file_name = ""
        file_content = ""
        current_section = ""
        next_line_file_content = False
        for _, line in enumerate(readme.split("\n")):
            if line.startswith("###"):
                # new section
                file_name = ""
                file_content = ""
                next_line_file_content = False
                current_section = line.split("### ")[1]
                test_cases[current_section] = {}
            elif "`:" in line:
                #  convention to get the filename
                result = file_name_in_markdown_pattern.findall(line)
                if len(result):
                    file_name = result[0]
            elif line.startswith("```") and not next_line_file_content:
                # only get inner content
                next_line_file_content = True
            elif line.startswith("```") and next_line_file_content:
                next_line_file_content = False
            elif next_line_file_content:
                file_content += f"{line}\n"

            if file_name and file_content and not next_line_file_content and current_section:
                test_cases[current_section].update({file_name: file_content})
                file_name = ""
                file_content = ""

    return test_cases


def create_test_files(test_case: dict[str, str]):
    shutil.rmtree("my_app", ignore_errors=True)  # cleanup
    for file_path, file_content in test_case.items():
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as file_to_create:
            file_to_create.write(file_content)


test_cases = extract_test_cases_from_readme()


@pytest.mark.parametrize("section_title", [("Getting Started"), ("Main Concept")])
def test_readme_simple(section_title):
    assert section_title in test_cases.keys()
    create_test_files(test_cases[section_title])

    # workaround since code gets changed during execution of test
    if section_title == "Main Concept":
        from my_app.api_with_constructors import app  # type: ignore
    else:
        from my_app.api import app  # type: ignore

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>Hello World</h1>" in response.text

    response = client.get("/customers", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<li>John Doe</li>" in response.text
    assert "<li>Jane Doe</li>" in response.text


def test_main_concept():
    assert "Main Concept" in test_cases.keys()
    create_test_files(test_cases["Main Concept"])

    from my_app.api_with_constructors import app  # type: ignore

    client = TestClient(app)

    response = client.get("/customers")
    assert response.status_code == 200
    assert "<h1>Hello World</h1>" in response.text
    assert "<li>John Doe</li>" in response.text
    assert "<li>Jane Doe</li>" in response.text


@pytest.mark.parametrize("headers", [{"HX-Request": "true"}, {}])
def test_hx_request_manually(headers: dict):
    assert "Handling `HX-Request` manually" in test_cases.keys()
    create_test_files(test_cases["Handling `HX-Request` manually"])

    from my_app.api_with_hx_request import app  # type: ignore

    client = TestClient(app)

    response = client.get("/email/123", headers=headers)
    assert response.status_code == 200
    assert "<p>123</p>" in response.text


def test_filters():
    assert "Filters" in test_cases.keys()
    create_test_files(test_cases["Filters"])

    from fastapi_htmx.htmx import templates_path

    assert templates_path.env.loader.searchpath == [str(Path("my_app") / "templates")]


@pytest.mark.parametrize(
    "case_name",
    ["Other template file extensions for SOME endpoints", "Other template file extensions for ALL endpoints"],
)
def test_template_extension_for_some_endpoints(case_name: str):
    assert case_name in test_cases.keys()
    create_test_files(test_cases[case_name])

    from my_app.api_template_file_extension import app  # type: ignore

    client = TestClient(app)

    response = client.get("/customers", headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert "<h1>Customer</h1>" in response.text


@pytest.mark.parametrize(
    "endpoint, expected_response_text",
    [
        ("/account", "<h1>My Account</h1>"),
        ("/products", "<h1>Products</h1>"),
    ],
)
def test_multiple_templates(endpoint: str, expected_response_text: str):
    case_name = "Multiple Template Directories"
    assert case_name in test_cases.keys()
    create_test_files(test_cases[case_name])

    from my_app.api_multiple_template_paths import app  # type: ignore

    client = TestClient(app)

    response = client.get(endpoint, headers={"HX-Request": "true"})
    assert response.status_code == 200
    assert expected_response_text in response.text
