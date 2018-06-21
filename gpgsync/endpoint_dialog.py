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
import queue
from PyQt5 import QtCore, QtWidgets, QtGui

from .endpoint import Endpoint, Verifier
from .status_bar import StatusBar, MessageQueue


class EndpointDialog(QtWidgets.QDialog):
    saved = QtCore.pyqtSignal(Endpoint)

    def __init__(self, common, endpoint=None):
        super(EndpointDialog, self).__init__()
        self.c = common

        # If endpoint == None, this is an add endpoint dialog. Otherwise, this
        # is an edit endpoint dialog
        if endpoint:
            self.setWindowTitle('Edit Endpoint')
            self.endpoint = endpoint
            self.new_endpoint = False
        else:
            self.setWindowTitle('Add Endpoint')
            self.endpoint = Endpoint(self.c)
            self.new_endpoint = True
        self.setMinimumWidth(400)

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
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_clicked)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_clicked)
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)

        # Status bar
        self.status_bar = StatusBar(self.c)
        self.status_bar.hide()

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
        layout.addWidget(self.status_bar)
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
        # Disable dialog
        self.setEnabled(False)

        # Get ready to verify
        self.status_bar.show()
        self.status_bar.show_loading()
        self.status_q = MessageQueue()
        self.update_ui_timer = QtCore.QTimer()
        self.update_ui_timer.timeout.connect(self.update_ui)
        self.update_ui_timer.start(500) # 0.5 seconds

        # Verify the endpoint
        fingerprint = self.fingerprint_edit.text().encode()
        url = self.url_edit.text().encode()
        keyserver = self.keyserver_edit.text().encode()
        use_proxy = self.use_proxy.isChecked()
        proxy_host = self.proxy_host_edit.text().encode()
        proxy_port = self.proxy_port_edit.text().encode()

        self.verifier = Verifier(self.c, self.status_q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
        self.verifier.alert_error.connect(self.verifier_alert_error)
        self.verifier.success.connect(self.verifier_success)
        self.verifier.finished.connect(self.verifier_finished)
        self.verifier.start()

    def cancel_clicked(self):
        self.close()

    def update_ui(self):
        # Update the status bar with events
        events = []
        done = False
        while not done:
            try:
                ev = self.status_q.get(False)
                events.append(ev)
            except queue.Empty:
                done = True

        for event in events:
            if event['type'] == 'update':
                print(event['msg'])
                self.status_bar.showMessage(event['msg'], event['timeout'])
            elif event['type'] == 'clear':
                self.status_bar.clearMessage()

    def verifier_alert_error(self, msg, details=''):
        # Alert the error
        self.c.alert(msg, details, QtWidgets.QMessageBox.Warning)

        # Re-enable dialog
        self.setEnabled(True)

    def verifier_success(self):
        # Update the endpoint values
        self.endpoint.fingerprint = self.fingerprint_edit.text().encode()
        self.endpoint.url = self.url_edit.text().encode()
        self.endpoint.sig_url = self.endpoint.url + b'.sig'
        self.endpoint.keyserver = self.keyserver_edit.text().encode()
        self.endpoint.use_proxy = self.use_proxy.isChecked()
        self.endpoint.proxy_host = self.proxy_host_edit.text().encode()
        self.endpoint.proxy_port = self.proxy_port_edit.text().encode()

        # Add the endpoint, if necessary
        if self.new_endpoint:
            self.c.log("EndpointDialog", "verifier_success", "adding endpoint")
            self.c.settings.endpoints.append(self.endpoint)

        # Save settings
        self.c.settings.save()

        self.saved.emit(self.endpoint)
        self.close()

    def verifier_finished(self):
        self.status_bar.clearMessage()
        self.status_bar.hide_loading()
        self.status_bar.hide()
        self.update_ui_timer.stop()
