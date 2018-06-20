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
import platform
from PyQt5 import QtCore, QtWidgets, QtGui

from .endpoint import Endpoint


class EndpointDialog(QtWidgets.QDialog):
    def __init__(self, common, endpoint=None):
        super(EndpointDialog, self).__init__()
        self.c = common

        # If endpoint == None, this is an add endpoint dialog. Otherwise, this
        # is an edit endpoint dialog
        if endpoint:
            self.endpoint = endpoint
        else:
            self.endpoint = Endpoint(self.c)

        if self.endpoint:
            self.setWindowTitle('Edit Endpoint')
        else:
            self.setWindowTitle('Add Endpoint')

        # Authority key fingerprint
        fingerprint_label = QtWidgets.QLabel("Authority Key Fingerprint")
        self.fingerprint_edit = QtWidgets.QLineEdit()

        # Fingerprints URL
        url_label = QtWidgets.QLabel("Fingerprints URL")
        self.url_edit = QtWidgets.QLineEdit()
        self.url_edit.setPlaceholderText("https://")
        self.url_edit.textChanged.connect(self.update_sig_url)
        self.sig_url = QtWidgets.QLabel()
        self.sig_url.setStyleSheet(self.c.css['EndpointDialog sig_url'])

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

        # Advanced settings button
        self.advanced_button = QtWidgets.QPushButton()
        self.advanced_button.setFlat(True)
        self.advanced_button.setStyleSheet(self.c.css['EndpointDialog advanced_button'])
        self.advanced_button.clicked.connect(self.toggle_advanced)

        # Advanced settings group
        advanced_layout = QtWidgets.QVBoxLayout()
        advanced_layout.addWidget(keyserver_label)
        advanced_layout.addWidget(self.keyserver_edit)
        advanced_layout.addWidget(proxy_group)
        self.advanced_group = QtWidgets.QGroupBox("Advanced Settings")
        self.advanced_group.setLayout(advanced_layout)

        # Buttons
        save_button = QtWidgets.QPushButton("Save")
        save_button.clicked.connect(self.save_clicked)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(fingerprint_label)
        layout.addWidget(self.fingerprint_edit)
        layout.addWidget(url_label)
        layout.addWidget(self.url_edit)
        layout.addWidget(self.sig_url)
        layout.addWidget(self.advanced_button)
        layout.addWidget(self.advanced_group)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        # Populate the widgets with endpoint data
        self.fingerprint_edit.setText(self.endpoint.fingerprint.decode())
        self.url_edit.setText(self.endpoint.url.decode())
        self.keyserver_edit.setText(self.endpoint.keyserver.decode())
        if self.endpoint.use_proxy:
            self.use_proxy.setCheckState(QtCore.Qt.Checked)
        else:
            self.use_proxy.setCheckState(QtCore.Qt.Unchecked)
        self.proxy_host_edit.setText(self.endpoint.proxy_host.decode())
        self.proxy_port_edit.setText(self.endpoint.proxy_port.decode())

        # Initially update the widgets
        self.update_sig_url(self.url_edit.text())
        self.advanced_group.show()
        self.toggle_advanced() # Hide advanced settings to start with

    def update_sig_url(self, text):
        if text == '':
            self.sig_url.hide()
        else:
            self.sig_url.show()
            self.sig_url.setText("Signature URL: {}.sig".format(text))

        self.adjustSize()

    def toggle_advanced(self):
        if self.advanced_group.isHidden():
            self.advanced_button.setText("Hide advanced settings")
            self.advanced_group.show()
        else:
            self.advanced_button.setText("Show advanced settings")
            self.advanced_group.hide()

        self.adjustSize()

    def save_clicked(self):
        pass

    def cancel_clicked(self):
        self.close()
