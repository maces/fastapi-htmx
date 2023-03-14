#!/bin/bash

new_version="$1"
description="$2"
if [ -n "$new_version" ]; then
    echo "specify a version"
    exit 1
fi
if [ -n "$description" ]; then
    echo "add a description"
    exit 1
fi

poetry version "$new_version"
git tag -a "$(poetry version --short)" -m "$description"
