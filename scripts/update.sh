#!/bin/bash
set -exo pipefail

SKIP_COMMIT=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-commit)
            SKIP_COMMIT=1
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--skip-commit]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--skip-commit]" >&2
            exit 2
            ;;
    esac
done

FIND_SCRIPT=$(dirname "$(readlink -f "$0")")/find_versions.py
LIBRARY_PATH=src/pbs_installer

python3 "$FIND_SCRIPT" "$LIBRARY_PATH/versions.json"

if [[ ! $(git status --porcelain) ]]; then
    echo "No changes to commit"
    exit 1
fi

if [[ $SKIP_COMMIT -eq 1 ]]; then
    echo "Skipping commit and tag creation"
    exit 0
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

if [ -n "$GITHUB_OUTPUT" ]; then
    echo "VERSION=$NEW_VERSION" >> "$GITHUB_OUTPUT"
fi

echo "All done!"
