#!/bin/bash

# See https://python-poetry.org/docs/repositories/#configuring-credentials
# on how to make sure not to save tokens in plain text on disk

# poetry config repositories.test-pypi https://test.pypi.org/legacy/
# poetry config pypi-token.test-pypi <your-token>
# poetry publish --build -r test-pypi

# poetry config repositories.pypi https://pypi.org/legacy/
# poetry config pypi-token.pypi <your-token>
poetry publish --build
