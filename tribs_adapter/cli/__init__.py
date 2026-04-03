import argparse
from .version_command import add_version_parser


def tribs_adapter_command():
    """Command line interface entrypoint function."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='Commands')
    subparsers.required = True

    # Add command parsers
    add_version_parser(subparsers)

    # Parse commandline arguments and call command function
    args = parser.parse_args()
    args.func(args)
