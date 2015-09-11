import sys
from PyQt4 import QtCore, QtGui

from endpoint_selection import EndpointSelection
from edit_endpoint import EditEndpoint
from endpoint import Endpoint

class PGPSync(QtGui.QWidget):
    def __init__(self, app):
        super(PGPSync, self).__init__()
        self.app = app
        self.setWindowTitle('PGP Sync')

        # List of configured endpoints
        self.current_endpoint = None
        self.endpoints = []
        # todo: load these from file

        # Endpoint selection GUI
        endpoint_selection = EndpointSelection()
        endpoint_selection_wrapper = QtGui.QWidget()
        endpoint_selection_wrapper.setLayout(endpoint_selection)

        endpoint_selection.add_endpoint_signal.connect(self.add_endpoint)

        # Edit endpoint GUI
        edit_endpoint = EditEndpoint()
        self.edit_endpoint_wrapper = QtGui.QWidget()
        self.edit_endpoint_wrapper.setLayout(edit_endpoint)
        self.edit_endpoint_wrapper.hide() # starts out hidden

        edit_endpoint.save_signal.connect(self.save_endpoint)
        edit_endpoint.delete_signal.connect(self.delete_endpoint)

        # Layout
        layout = QtGui.QHBoxLayout()
        layout.addWidget(endpoint_selection_wrapper)
        layout.addWidget(self.edit_endpoint_wrapper)
        self.setLayout(layout)
        self.show()

    def add_endpoint(self):
        self.endpoints.append(Endpoint())
        self.endpoint_selection.refresh(self.endpoints)

    def save_endpoint(self):
        print 'save endpoint'
        self.edit_endpoint_wrapper.hide()

    def delete_endpoint(self):
        print 'delete endpoint'
        self.edit_endpoint_wrapper.hide()

def main():
    app = QtGui.QApplication(sys.argv)
    gui = PGPSync(app)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
