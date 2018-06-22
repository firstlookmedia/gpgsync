# -*- coding: utf-8 -*-
import pytest
import sys
from PyQt5 import QtWidgets

from gpgsync.common import Common

# Set GPG Sync to dev mode, so it looks for resources in the right place
sys.gpgsync_dev = True

# Setup Qt
qt_app = QtWidgets.QApplication(sys.argv)

# Generate a Common singleton
@pytest.fixture
def common():
    return Common(debug=False)
