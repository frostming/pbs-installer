from __future__ import annotations

import hashlib
import os
import tempfile
from typing import TYPE_CHECKING
from urllib.parse import unquote

import requests

from ._utils import get_arch_platform

if TYPE_CHECKING:
    from _typeshed import StrPath

THIS_ARCH, THIS_PLATFORM = get_arch_platform()


def _get_headers() -> dict[str, str] | None:
    TOKEN = os.getenv("GITHUB_TOKEN")
    if TOKEN is None:
        return None
    return {
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {TOKEN}",
    }


def get_download_link(request: str) -> str:
    from ._versions import PYTHON_VERSIONS

    for py_ver, urls in PYTHON_VERSIONS.items():
        if not py_ver.matches(request):
            continue

        for arch, platform, url in urls:
            if (arch, platform) == (THIS_ARCH, THIS_PLATFORM):
                return url
            else:
                break
    raise ValueError(f"Could not find a CPython {request!r} matching this system")


def _read_sha256(url: str, sess: requests.Session) -> str | None:
    resp = sess.get(url + ".sha256", headers=_get_headers())
    if not resp.ok:
        return None
    return resp.text.strip()


def download(url: str, destination: StrPath, session: requests.Session | None = None) -> str:
    filename = unquote(url.rsplit("/")[-1])
    if session is None:
        session = requests.Session()

    hasher = hashlib.sha256()
    checksum = _read_sha256(url, session)

    with open(destination, "wb") as f:
        response = session.get(url, stream=True, headers=_get_headers())
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            if checksum:
                hasher.update(chunk)
            f.write(chunk)

    if checksum and hasher.hexdigest() != checksum:
        raise RuntimeError(f"Checksum mismatch. Expected {checksum}, got {hasher.hexdigest()}")
    return filename


def install_file(
    filename: StrPath, destination: StrPath, original_filename: str | None = None
) -> None:
    import tarfile

    import zstandard as zstd

    if original_filename is None:
        original_filename = str(filename)

    if original_filename.endswith(".zst"):
        dctx = zstd.ZstdDecompressor()
        with tempfile.TemporaryFile(suffix=".tar") as ofh:
            with open(filename, "rb") as ifh:
                dctx.copy_stream(ifh, ofh)
            ofh.seek(0)
            with tarfile.open(fileobj=ofh) as z:
                z.extractall(destination)

    else:
        with tarfile.open(filename) as z:
            z.extractall(destination)


def install(request: str, destination: StrPath, session: requests.Session | None = None) -> None:
    """Download and install the requested python version"""
    url = get_download_link(request)
    with tempfile.NamedTemporaryFile() as tf:
        tf.close()
        original_filename = download(url, tf.name, session)
        install_file(tf.name, destination, original_filename)
