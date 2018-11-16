# -*- coding: utf-8 -*-
import pytest
import sys
import tempfile
from PyQt5 import QtWidgets

from gpgsync.common import Common
from gpgsync.gnupg import GnuPG
from gpgsync.keylist import Keylist, LegacyKeylist

# Set GPG Sync to dev mode, so it looks for resources in the right place
sys.gpgsync_dev = True

# Setup Qt
qt_app = QtWidgets.QApplication(sys.argv)


# Generate a Common singleton
@pytest.fixture
def common():
    appdata_path = tempfile.mkdtemp()

    common = Common(debug=False)
    common.gpg = GnuPG(common, appdata_path=appdata_path)
    return common


# Generate an keylist
@pytest.fixture
def keylist(common):
    return Keylist(common)


# Generate an legacy keylist
@pytest.fixture
def legacy_keylist(common):
    return LegacyKeylist(common)
