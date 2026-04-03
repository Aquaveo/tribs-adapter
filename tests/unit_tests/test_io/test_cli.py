from unittest.mock import patch
from tribs_adapter.cli import tribs_adapter_command

from tribs_adapter import __version__


@patch('builtins.print')
def test_cli_command(mock_print):
    with patch('sys.argv', ['tribs-adapter', 'version']):
        tribs_adapter_command()
        mock_print.assert_called_once_with(__version__)
