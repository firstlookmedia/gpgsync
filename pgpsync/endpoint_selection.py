import re
from PyQt4 import QtCore, QtGui

class EndpointList(QtGui.QListWidget):
    def __init__(self):
        super(EndpointList, self).__init__()

    def add_endpoint_error(self, error):
        item = QtGui.QListWidgetItem(error)
        item.setForeground(QtGui.QBrush(QtGui.QColor(200, 0, 0)))
        self.addItem(item)

    def refresh(self, endpoints):
        self.clear()

        for e in endpoints:
            if not re.match(r'^[a-fA-F\d]{40}$', e.fingerprint):
                self.add_endpoint_error('Not configured')
                continue

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
