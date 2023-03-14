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
