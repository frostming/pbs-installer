#!/bin/bash
set -eo pipefail

FIND_SCRIPT=$(dirname "$(readlink -f "$0")")/find_versions.py
LIBRARY_PATH=src/pbs_installer

python3 "$FIND_SCRIPT" "$LIBRARY_PATH/_versions.py"

pipx run ruff format $LIBRARY_PATH

if [[ ! $(git status --porcelain) ]]; then
  echo "No changes to commit"
  exit 1
fi
# get the current date in YYYY.M.d format
DATE_TAG=$(date +%Y.%-m.%-d)

echo "Commit new files"
set -x
git add "$LIBRARY_PATH/"
git commit -m "Bump version to $DATE_TAG"
git tag -a "$DATE_TAG" -m "Bump version to $DATE_TAG"
set +x

echo "All done!"
