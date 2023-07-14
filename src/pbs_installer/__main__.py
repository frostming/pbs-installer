import logging
from argparse import ArgumentParser

from ._install import install


def _setup_logger(verbose: bool):
    logger = logging.getLogger("pbs_installer")
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.WARNING)


def main():
    parser = ArgumentParser("pbs-install", description="Installer for Python Build Standalone")
    parser.add_argument("version", help="The version of Python to install, e.g. 3.8,3.10.4")
    parser.add_argument(
        "--version-dir", help="Install to a subdirectory named by the version", action="store_true"
    )
    parser.add_argument("-v", "--verbose", help="Enable verbose logging", action="store_true")
    parser.add_argument("-d", "--destination", help="The directory to install to", required=True)

    args = parser.parse_args()
    _setup_logger(args.verbose)
    install(args.version, args.destination, version_dir=args.version_dir)
    print("Done!")


if __name__ == "__main__":
    main()
