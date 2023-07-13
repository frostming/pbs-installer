from __future__ import annotations

import tarfile
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from _typeshed import StrPath

ARCH_MAPPING = {
    "aarch64": "arm64",
    "amd64": "x86_64",
}


class PythonVersion(NamedTuple):
    kind: str
    major: int
    minor: int
    micro: int

    def __str__(self) -> str:
        return f"{self.kind}@{self.major}.{self.minor}.{self.micro}"

    def matches(self, request: str) -> bool:
        try:
            parts = tuple(int(v) for v in request.split("."))
        except ValueError:
            raise ValueError(
                f"Invalid version: {request!r}, each part must be an integer"
            ) from None

        if len(parts) < 1:
            raise ValueError("Version must have at least one part")

        if parts[0] != self.major:
            return False
        if len(parts) > 1 and parts[1] != self.minor:
            return False
        if len(parts) > 2 and parts[2] != self.micro:
            return False
        return True


def get_arch_platform() -> tuple[str, str]:
    import platform

    plat = platform.system().lower()
    arch = platform.machine().lower()
    return ARCH_MAPPING.get(arch, arch), plat


def unpack_tar(tf: tarfile.TarFile, destination: StrPath, skip_parts: int = 0) -> None:
    """Unpack the tarfile to the destination, with the first skip_parts parts of the path removed"""
    for member in tf.getmembers():
        fn = member.name.lstrip("/")
        parts = fn.split("/")
        fn = "/".join(parts[skip_parts:])
        member.name = fn
        tf.extract(member, destination)
