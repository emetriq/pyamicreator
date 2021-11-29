import pytest
import sys
sys.path.insert(0, 'src')
from pyamicreator.app import Cli, main
from fire.core import FireExit

__author__ = "Slash Gordon"
__copyright__ = "Slash Gordon"
__license__ = "MIT"


def test_image():
    cli = Cli()
    with pytest.raises(FileNotFoundError):
        cli.create_image('test.config', '', '','')
