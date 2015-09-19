# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtCore, QtWidgets

qt_app = None

def setup_qt():
    global qt_app
    if not qt_app:
        qt_app = QtWidgets.QApplication(sys.argv)
