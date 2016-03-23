# -*- coding: utf-8 -*-
import sys, os, subprocess, shutil
from PyQt5 import QtCore, QtWidgets

qt_app = None

def setup_qt():
    global qt_app
    if not qt_app:
        qt_app = QtWidgets.QApplication(sys.argv)

# GnuPG related test helpers
test_key_fp = b'ABCFD99FA1617E55B8CDE5ADE36FD670777947EB'

def get_gpg_file(filename):
    return os.path.join(os.path.abspath('test/gpg_files'), filename)

def import_key(filename, homedir):
    subprocess.call(['gpg', '--homedir', homedir, '--import', get_gpg_file(filename)],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)

# Endpoint related test helpers
def get_endpoint_file_content(filename):
    filename = os.path.join(os.path.abspath('test/endpoint_files'), filename)
    return open(filename, 'rb').read()
