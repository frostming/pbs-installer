#!/bin/bash
set -exo pipefail

FIND_SCRIPT=$(dirname "$(readlink -f "$0")")/find_versions.py
LIBRARY_PATH=src/pbs_installer

python3 "$FIND_SCRIPT" "$LIBRARY_PATH/_versions.py"

pipx run ruff format $LIBRARY_PATH

if [[ ! $(git status --porcelain) ]]; then
    echo "No changes to commit"
    exit 1
fi
if [ -n "$TARGET_VERSION" ]; then
    NEW_VERSION=$TARGET_VERSION
else
    # get the current date in YYYY.M.d format
    NEW_VERSION=$(date +%Y.%-m.%-d)
fi

echo "Commit new files"
set -x
git add "$LIBRARY_PATH/"
git commit -m "Bump version to $NEW_VERSION"
git tag -a "$NEW_VERSION" -m "Bump version to $NEW_VERSION"
set +x

echo "All done!"
