from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import NamedTuple, Tuple

TOKEN = os.getenv("GITHUB_TOKEN")
if TOKEN is None:
    raise RuntimeError("GITHUB_TOKEN is not set")
RELEASE_URL = "https://api.github.com/repos/indygreg/python-build-standalone/releases"
HEADERS = {
    "X-GitHub-Api-Version": "2022-11-28",
    "Authorization": f"Bearer {TOKEN}",
}
FLAVOR_PREFERENCES = [
    "shared-pgo",
    "shared-noopt",
    "shared-noopt",
    "static-noopt",
    "gnu-pgo+lto",
    "gnu-lto",
    "gnu-pgo",
    "pgo+lto",
    "lto",
    "pgo",
]
HIDDEN_FLAVORS = [
    "debug",
    "noopt",
    "install_only",
]
SPECIAL_TRIPLES = {
    "macos": "x86_64-apple-darwin",
    "linux64": "x86_64-unknown-linux",
    "windows-amd64": "x86_64-pc-windows",
    "windows-x86": "i686-pc-windows",
    "linux64-musl": "x86_64-unknown-linux",
}

ARCH_MAPPING = {
    "x86_64": "x86_64",
    "x86": "i686",
    "i686": "i686",
    "aarch64": "arm64",
}

PLATFORM_MAPPING = {
    "darwin": "darwin",
    "windows": "windows",
    "linux": "linux",
}


_filename_re = re.compile(
    r"""(?x)
    ^
        cpython-(?P<ver>\d+\.\d+\.\d+?)
        (?:\+\d+)?
        -(?P<triple>.*?)
        (?:-[\dT]+)?\.tar\.(?:gz|zst)
    $
"""
)
_suffix_re = re.compile(
    r"""(?x)^(.*?)-(%s)$"""
    % (
        "|".join(
            map(
                re.escape,
                sorted(FLAVOR_PREFERENCES + HIDDEN_FLAVORS, key=len, reverse=True),
            )
        )
    )
)


class _AssetInfo(NamedTuple):
    tuple: tuple[str, str]
    flavor: str | None
    url: str


PyVersion = Tuple[int, int, int]


def parse_filename(filename: str) -> tuple[str, str, str | None] | None:
    match = _filename_re.match(filename)
    if match is None:
        return
    version, triple = match.groups()
    if triple.endswith("-full"):
        triple = triple[:-5]
    match = _suffix_re.match(triple)
    if match is not None:
        triple, suffix = match.groups()
    else:
        suffix = None
    return (version, triple, suffix)


def normalize_triple(triple: str) -> tuple[str, str] | None:
    if "-musl" in triple or "-static" in triple:
        return
    triple = SPECIAL_TRIPLES.get(triple, triple)
    pieces = triple.split("-")
    try:
        arch = ARCH_MAPPING.get(pieces[0])
        if arch is None:
            return
        platform = PLATFORM_MAPPING.get(pieces[2])
        if platform is None:
            return
    except IndexError:
        return
    return arch, platform


async def get_releases() -> dict[PyVersion, dict[tuple[str, str], str]]:
    import httpx

    results: dict[str, list[_AssetInfo]] = {}
    async with httpx.AsyncClient(follow_redirects=True, headers=HEADERS) as sess:
        for page in range(1, 100):
            resp = await sess.get(RELEASE_URL, params={"page": page})
            await resp.aread()
            rows = resp.json()
            if not rows:
                break
            for row in rows:
                for asset in row["assets"]:
                    url = asset["browser_download_url"]
                    base_name = asset["name"]
                    if base_name.endswith(".sha256"):
                        continue
                    info = parse_filename(base_name)
                    if info is None:
                        continue
                    py_ver, triple, flavor = info
                    if "-static" in triple or (flavor and "noopt" in flavor):
                        continue
                    triple = normalize_triple(triple)
                    if triple is None:
                        continue
                    results.setdefault(py_ver, []).append(_AssetInfo(triple, flavor, url))

    final_results: dict[PyVersion, dict[tuple[str, str], str]] = {}
    for py_ver, choices in results.items():
        choices.sort(key=_sort_key)
        urls = {}
        for triple, flavor, url in choices:
            if triple in urls:
                continue
            urls[triple] = url
        final_results[tuple(map(int, py_ver.split(".")))] = urls
    return final_results


def _sort_key(info: _AssetInfo) -> int:
    flavor = info.flavor
    pref = len(FLAVOR_PREFERENCES) + 1
    if flavor is not None:
        try:
            pref = FLAVOR_PREFERENCES.index(flavor)
        except ValueError:
            pass
    return pref


_date_re = re.compile(r"(\d{4})(\d{2})(\d{2})")


def tag_to_version(tag: str) -> str:
    match = _date_re.match(tag)
    if match is None:
        return tag
    return f"{match.group(1)}.{int(match.group(2))}.{int(match.group(3))}"


async def main():
    args = sys.argv[1:]
    if len(args) < 1:
        sys.exit("Usage: %s <target_file>" % sys.argv[0])

    final_results = await get_releases()

    with open(args[0], "w") as f:
        print("# code @generated by pbs-installer/find_versions.py, do not edit", file=f)
        print("from __future__ import annotations\n", file=f)
        print("from ._utils import PythonVersion", file=f)
        print("PYTHON_VERSIONS: dict[PythonVersion, list[tuple[str, str, str]]] = {", file=f)
        for interpreter, py_ver, choices in sorted(
            (("cpython",) + x for x in final_results.items()),
            key=lambda x: x[:2],
            reverse=True,
        ):
            print("    PythonVersion(%r, %s, %s, %s): [" % (interpreter, *py_ver), file=f)
            for (arch, platform), url in sorted(choices.items()):
                print(f"({arch!r}, {platform!r}, {url!r}),", file=f)
            print("],", file=f)
        print("}", file=f)
        print("python versions are successfully written to", args[0])


if __name__ == "__main__":
    asyncio.run(main())
