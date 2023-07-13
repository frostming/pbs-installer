from argparse import ArgumentParser

from ._install import install


def main():
    parser = ArgumentParser("pbs-install")
    parser.add_argument("version", help="The version of Python to install, e.g. 3.8,3.10.4")
    parser.add_argument("-d", "--destination", help="The directory to install to", required=True)

    args = parser.parse_args()
    install(args.version, args.destination)
    print("Done!")


if __name__ == "__main__":
    main()
