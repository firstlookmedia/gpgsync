import re
from PyQt4 import QtCore, QtGui

import common

class EndpointList(QtGui.QListWidget):
    def __init__(self):
        super(EndpointList, self).__init__()

    def add_endpoint_error(self, e, error):
        item = QtGui.QListWidgetItem(error)
        item.endpoint = e
        item.setForeground(QtGui.QBrush(QtGui.QColor(200, 0, 0)))
        self.addItem(item)

    def add_endpoint(self, e):
        item = QtGui.QListWidgetItem('Configured')
        item.endpoint = e
        self.addItem(item)

    def refresh(self, endpoints):
        self.clear()

        for e in endpoints:
            if not common.valid_fp(e.fingerprint):
                self.add_endpoint_error(e, 'Not configured')
                continue

            self.add_endpoint(e)

class EndpointSelection(QtGui.QVBoxLayout):
    add_endpoint_signal = QtCore.pyqtSignal()

    def __init__(self):
        super(EndpointSelection, self).__init__()

        self.endpoint_list = EndpointList()

        self.add_btn = QtGui.QPushButton("Add Endpoint")
        self.add_btn.clicked.connect(self.add_endpoint)

        self.addWidget(self.endpoint_list)
        self.addWidget(self.add_btn)

    def add_endpoint(self):
        self.add_endpoint_signal.emit()

    def refresh(self, endpoints):
        self.endpoint_list.refresh(endpoints)
