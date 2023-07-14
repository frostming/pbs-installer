from __future__ import annotations

import hashlib
import logging
import os
import tempfile
from typing import TYPE_CHECKING
from urllib.parse import unquote

from ._utils import PythonVersion, get_arch_platform, unpack_tar

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import requests
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


def get_download_link(request: str) -> tuple[PythonVersion, str]:
    """Get the download URL matching the given requested version.

    :param request: The version of Python to install, e.g. 3.8,3.10.4
    :return: A tuple of the PythonVersion and the download URL
    """
    from ._versions import PYTHON_VERSIONS

    for py_ver, urls in PYTHON_VERSIONS.items():
        if not py_ver.matches(request):
            continue

        for arch, platform, url in urls:
            logger.debug(
                "Checking %s %s with current system %s %s", arch, platform, THIS_ARCH, THIS_PLATFORM
            )
            if (arch, platform) == (THIS_ARCH, THIS_PLATFORM):
                return py_ver, url
        break
    raise ValueError(f"Could not find a CPython {request!r} matching this system")


def _read_sha256(url: str, sess: requests.Session) -> str | None:
    resp = sess.get(url + ".sha256", headers=_get_headers())
    if not resp.ok:
        logger.warning("No checksum found for %s, this would be insecure", url)
        return None
    return resp.text.strip()


def download(url: str, destination: StrPath, session: requests.Session | None = None) -> str:
    """Download the given url to the destination.

    :param url: The url to download
    :param destination: The file path to download to
    :param session: A requests session to use for downloading, or None to create a new one
    :return: The original filename of the downloaded file
    """
    logger.debug("Downloading url %s to %s", url, destination)
    filename = unquote(url.rsplit("/")[-1])
    try:
        import requests
    except ModuleNotFoundError:
        raise RuntimeError("You must install requests to use this function") from None

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
    """Unpack the downloaded file to the destination.

    :param filename: The file to unpack
    :param destination: The directory to unpack to
    :param original_filename: The original filename of the file, if it was renamed
    """

    import tarfile

    import zstandard as zstd

    if original_filename is None:
        original_filename = str(filename)
    logger.debug(
        "Extracting file %s to %s with original filename %s",
        filename,
        destination,
        original_filename,
    )
    if original_filename.endswith(".zst"):
        dctx = zstd.ZstdDecompressor()
        with tempfile.TemporaryFile(suffix=".tar") as ofh:
            with open(filename, "rb") as ifh:
                dctx.copy_stream(ifh, ofh)
            ofh.seek(0)
            with tarfile.open(fileobj=ofh) as z:
                unpack_tar(z, destination, 1)

    else:
        with tarfile.open(filename) as z:
            unpack_tar(z, destination, 1)


def install(
    request: str,
    destination: StrPath,
    version_dir: bool = False,
    session: requests.Session | None = None,
) -> None:
    """Download and install the requested python version.

    :param request: The version of Python to install, e.g. 3.8,3.10.4
    :param destination: The directory to install to
    :param version_dir: Whether to install to a subdirectory named with the python version
    :param session: A requests session to use for downloading
    """
    ver, url = get_download_link(request)
    if version_dir:
        destination = os.path.join(destination, str(ver))
    logger.debug("Installing %s to %s", ver, destination)
    os.makedirs(destination, exist_ok=True)
    with tempfile.NamedTemporaryFile() as tf:
        tf.close()
        original_filename = download(url, tf.name, session)
        install_file(tf.name, destination, original_filename)
