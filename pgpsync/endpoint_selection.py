import re
from PyQt5 import QtCore, QtWidgets, QtGui

from . import common

class EndpointList(QtWidgets.QListWidget):
    def __init__(self, gpg):
        super(EndpointList, self).__init__()
        self.gpg = gpg

    def add_endpoint_error(self, e, error):
        item = QtWidgets.QListWidgetItem(error)
        item.endpoint = e
        item.setForeground(QtGui.QBrush(QtGui.QColor(200, 0, 0)))
        self.addItem(item)

    def add_endpoint(self, e):
        uid = self.gpg.get_uid(e.fingerprint)
        keyid = common.fp_to_keyid(e.fingerprint)
        last_updated_time = 'never' # TODO: Fix this

        s = '{}\n{}\nLast updated: {}'.format(uid, keyid, last_updated_time)

        item = QtWidgets.QListWidgetItem(s)
        item.endpoint = e
        self.addItem(item)

    def refresh(self, endpoints):
        self.clear()

        for e in endpoints:
            if not common.valid_fp(e.fingerprint):
                self.add_endpoint_error(e, 'Not configured')
                continue

            self.add_endpoint(e)

class EndpointSelection(QtWidgets.QVBoxLayout):
    add_endpoint_signal = QtCore.pyqtSignal()

    def __init__(self, gpg):
        super(EndpointSelection, self).__init__()
        self.gpg = gpg

        self.endpoint_list = EndpointList(gpg)

        self.add_btn = QtWidgets.QPushButton("Add Endpoint")
        self.add_btn.clicked.connect(self.add_endpoint)

        self.addWidget(self.endpoint_list)
        self.addWidget(self.add_btn)

    def add_endpoint(self):
        self.add_endpoint_signal.emit()

    def refresh(self, endpoints):
        self.endpoint_list.refresh(endpoints)
