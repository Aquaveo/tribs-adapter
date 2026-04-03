from tribs_adapter import __version__


def add_version_parser(subparsers):
    version_parser = subparsers.add_parser('version', help='Current version.')
    version_parser.set_defaults(func=version_command)


def version_command(args):
    print(__version__)
