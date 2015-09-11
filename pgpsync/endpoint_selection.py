from PyQt4 import QtCore, QtGui

class EndpointList(QtGui.QListWidget):
    def __init__(self):
        super(EndpointList, self).__init__()

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
        for e in endpoints:
            pass
