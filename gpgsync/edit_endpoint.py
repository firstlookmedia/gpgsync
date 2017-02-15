# -*- coding: utf-8 -*-
"""
GPG Sync
Helps users have up-to-date public keys for everyone in their organization
https://github.com/firstlookmedia/gpgsync
Copyright (C) 2016 First Look Media

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from PyQt5 import QtCore, QtWidgets

from .endpoint import Endpoint
from .loading_animation import LoadingAnimation
from . import common

class EditEndpoint(QtWidgets.QVBoxLayout):
    save_signal = QtCore.pyqtSignal()
    delete_signal = QtCore.pyqtSignal()

    def __init__(self):
        super(EditEndpoint, self).__init__()
        self.endpoint = None

        # Signing key fingerprint
        fingerprint_label = QtWidgets.QLabel("GPG Fingerprint")
        self.fingerprint_edit = QtWidgets.QLineEdit()

        # Fingerprints URL
        url_label = QtWidgets.QLabel("Fingerprints URL")
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("https://")

        # Signature URL
        sig_url_label = QtWidgets.QLabel("Signature URL")
        self.sig_url_edit = QtWidgets.QLineEdit()
        self.sig_url_edit.setEnabled(False)
        self.url_edit.textChanged.connect(self.update_sig_url)

        # Keyserver
        keyserver_label = QtWidgets.QLabel("Key server")
        self.keyserver_edit = QtWidgets.QLineEdit()

        # SOCKS5 proxy settings
        self.use_proxy = QtWidgets.QCheckBox()
        self.use_proxy.setText("Load URL through SOCKS5 proxy (e.g. Tor)")
        self.use_proxy.setCheckState(QtCore.Qt.Unchecked)

        proxy_host_label = QtWidgets.QLabel('Host')
        self.proxy_host_edit = QtWidgets.QLineEdit()
        proxy_port_label = QtWidgets.QLabel('Port')
        self.proxy_port_edit = QtWidgets.QLineEdit()

        proxy_hlayout = QtWidgets.QHBoxLayout()
        proxy_hlayout.addWidget(proxy_host_label)
        proxy_hlayout.addWidget(self.proxy_host_edit)
        proxy_hlayout.addWidget(proxy_port_label)
        proxy_hlayout.addWidget(self.proxy_port_edit)

        proxy_vlayout = QtWidgets.QVBoxLayout()
        proxy_vlayout.addWidget(self.use_proxy)
        proxy_vlayout.addLayout(proxy_hlayout)

        proxy_group = QtWidgets.QGroupBox("Proxy Configuration")
        proxy_group.setLayout(proxy_vlayout)

        # Buttons
        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self.save)
        self.delete_btn = QtWidgets.QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)

        # Add all the widgets to the layout
        self.addWidget(fingerprint_label)
        self.addWidget(self.fingerprint_edit)
        self.addStretch(1)
        self.addWidget(url_label)
        self.addWidget(self.url_edit)
        self.addStretch(1)
        self.addWidget(sig_url_label)
        self.addWidget(self.sig_url_edit)
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

        self.fingerprint_edit.setText(endpoint.fingerprint.decode())
        if endpoint.url.decode():
            self.url_edit.setText(endpoint.url.decode())
        self.keyserver_edit.setText(endpoint.keyserver.decode())

        if endpoint.use_proxy:
            self.use_proxy.setCheckState(QtCore.Qt.Checked)
        else:
            self.use_proxy.setCheckState(QtCore.Qt.Unchecked)

        self.proxy_host_edit.setText(endpoint.proxy_host.decode())
        proxy_port_label = QtWidgets.QLabel('Port')
        self.proxy_port_edit.setText(endpoint.proxy_port.decode())

    def save(self):
        self.save_signal.emit()

    def delete(self):
        self.delete_signal.emit()

    def update_sig_url(self, text):
        self.sig_url_edit.setText("{}.sig".format(text))
