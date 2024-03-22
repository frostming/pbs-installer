# Welcome to the documentation of pbs-installer

An installer for [@indygreg](https://github.com/indygreg)'s [python-build-standalone](https://github.com/indygreg/python-build-standalone)

## Installation

It's highly recommended to install `pbs-installer` with [`pipx`](https://github.com/pypa/pipx):

```bash
pipx install pbs-installer
```

Or more conviniently, you can run with `pipx` directly:

```bash
pipx run pbs-installer --help
```

## Usage

::: pbs_installer
    options:
      heading_level: 3
      show_docstring_modules: false

## CLI Usage

`pbs-installer` also ships with a CLI named `pbs-install`:

```bash
usage: pbs-install [-h] [--version-dir] -d DESTINATION [--arch {arm64,i686,x86_64}] [--platform {darwin,linux,windows}] [-v] [-l] version

Installer for Python Build Standalone

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose logging
  -l, --list            List installable versions

Install Arguments:
  version               The version of Python to install, e.g. 3.8,3.10.4
  --version-dir         Install to a subdirectory named by the version
  -d DESTINATION, --destination DESTINATION
                        The directory to install to
  --arch {arm64,i686,x86_64}
                        Override the architecture to install
  --platform {darwin,linux,windows}
                        Override the platform to install
```
