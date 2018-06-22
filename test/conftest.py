# -*- coding: utf-8 -*-
import pytest
import sys
import tempfile
from PyQt5 import QtWidgets

from gpgsync.common import Common
from gpgsync.gnupg import GnuPG
from gpgsync.endpoint import Endpoint

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


# Generate an endpint
@pytest.fixture
def endpoint():
    c = common()
    return Endpoint(c)
