#!/bin/bash

new_version="$1"
description="$2"
if [ -z "$new_version" ]; then
    echo "specify a version"
    exit 1
fi
if [ -z "$description" ]; then
    echo "add a description"
    exit 1
fi

poetry version "$new_version"
git add pyproject.toml
git commit -m "$description"
git tag -a "$(poetry version --short)" -m "$description"
