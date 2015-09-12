from PyQt4 import QtCore, QtGui

from endpoint import Endpoint
import common

class EditEndpoint(QtGui.QVBoxLayout):
    save_signal = QtCore.pyqtSignal()
    delete_signal = QtCore.pyqtSignal()

    def __init__(self):
        super(EditEndpoint, self).__init__()
        self.endpoint = None

        # Signing key fingerprint
        fingerprint_label = QtGui.QLabel("Signing key fingerprint")
        self.fingerprint_edit = QtGui.QLineEdit()

        # Signed-fingerprints URL
        url_label = QtGui.QLabel("Signed fingerprints URL")
        self.url_edit = QtGui.QLineEdit()

        # Keyserver
        keyserver_label = QtGui.QLabel("Key server")
        self.keyserver_edit = QtGui.QLineEdit()

        # SOCKS5 proxy settings
        self.use_proxy = QtGui.QCheckBox()
        self.use_proxy.setText("Load URL through SOCKS5 proxy (e.g. Tor)")
        self.use_proxy.setCheckState(QtCore.Qt.Unchecked)

        proxy_host_label = QtGui.QLabel('Host')
        self.proxy_host_edit = QtGui.QLineEdit()
        proxy_port_label = QtGui.QLabel('Port')
        self.proxy_port_edit = QtGui.QLineEdit()

        proxy_hlayout = QtGui.QHBoxLayout()
        proxy_hlayout.addWidget(proxy_host_label)
        proxy_hlayout.addWidget(self.proxy_host_edit)
        proxy_hlayout.addWidget(proxy_port_label)
        proxy_hlayout.addWidget(self.proxy_port_edit)

        proxy_vlayout = QtGui.QVBoxLayout()
        proxy_vlayout.addWidget(self.use_proxy)
        proxy_vlayout.addLayout(proxy_hlayout)

        proxy_group = QtGui.QGroupBox("Proxy Configuration")
        proxy_group.setLayout(proxy_vlayout)

        # Buttons
        self.save_btn = QtGui.QPushButton("Save")
        self.save_btn.clicked.connect(self.save)
        self.delete_btn = QtGui.QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete)
        self.loading_animation = common.LoadingAnimation()
        self.loading_animation.hide()

        button_layout = QtGui.QHBoxLayout()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.loading_animation)

        # Add all the widgets to the layout
        self.addWidget(fingerprint_label)
        self.addWidget(self.fingerprint_edit)
        self.addStretch(1)
        self.addWidget(url_label)
        self.addWidget(self.url_edit)
        self.addStretch(1)
        self.addWidget(keyserver_label)
        self.addWidget(self.keyserver_edit)
        self.addStretch(1)
        self.addWidget(proxy_group)
        self.addStretch(1)
        self.addLayout(button_layout)
        self.addStretch(1)

    def set_endpoint(self, endpoint):
        self.endpoint = endpoint
        self.loading_animation.hide()

        self.fingerprint_edit.setText(endpoint.fingerprint)
        self.url_edit.setText(endpoint.url)
        self.keyserver_edit.setText(endpoint.keyserver)

        if endpoint.use_proxy:
            self.use_proxy.setCheckState(QtCore.Qt.Checked)
        else:
            self.use_proxy.setCheckState(QtCore.Qt.Unchecked)

        self.proxy_host_edit.setText(endpoint.proxy_host)
        proxy_port_label = QtGui.QLabel('Port')
        self.proxy_port_edit.setText(endpoint.proxy_port)

    def save(self):
        self.loading_animation.show()
        self.save_signal.emit()

    def delete(self):
        self.delete_signal.emit()
