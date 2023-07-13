from typing import NamedTuple

ARCH_MAPPING = {
    "aarch64": "arm64",
    "amd64": "x86_64",
}


class PythonVersion(NamedTuple):
    kind: str
    major: int
    minor: int
    micro: int

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
