from PyQt4 import QtCore, QtGui

def alert(msg, icon=QtGui.QMessageBox.Warning):
    d = QtGui.QMessageBox()
    d.setWindowTitle('PGP Sync')
    d.setText(msg)
    d.setIcon(icon)
    d.exec_()
