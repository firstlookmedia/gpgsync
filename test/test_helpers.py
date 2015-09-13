import sys
from PyQt4 import QtCore, QtGui

qt_app = None

def setup_qt():
    global qt_app
    if not qt_app:
        qt_app = QtGui.QApplication(sys.argv)
