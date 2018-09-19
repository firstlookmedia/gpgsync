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

from .keylist import Keylist, Verifier, VerifierMessageQueue


class KeylistDialog(QtWidgets.QDialog):
    saved = QtCore.pyqtSignal(Keylist)

    def __init__(self, common, keylist=None):
        super(KeylistDialog, self).__init__()
        self.c = common

        # If keylist == None, this is an add keylist dialog. Otherwise, this
        # is an edit keylist dialog
        if keylist:
            self.setWindowTitle('Edit Keylist')
            self.keylist = keylist
            self.new_keylist = False
        else:
            self.setWindowTitle('Add Keylist')
            self.keylist = Keylist(self.c)
            self.new_keylist = True
        self.setWindowIcon(self.c.icon)
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
        self.sig_url.setStyleSheet(self.c.css['KeylistDialog sig_url'])

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
        self.advanced_button.setStyleSheet(self.c.css['KeylistDialog advanced_button'])
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

        # Populate the widgets with keylist data
        self.fingerprint_edit.setText(self.keylist.fingerprint.decode())
        self.url_edit.setText(self.keylist.url.decode())
        self.keyserver_edit.setText(self.keylist.keyserver.decode())
        if self.keylist.use_proxy:
            self.use_proxy.setCheckState(QtCore.Qt.Checked)
        else:
            self.use_proxy.setCheckState(QtCore.Qt.Unchecked)
        self.proxy_host_edit.setText(self.keylist.proxy_host.decode())
        self.proxy_port_edit.setText(self.keylist.proxy_port.decode())

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
        # Grab the values
        fingerprint = self.fingerprint_edit.text().encode()
        url = self.url_edit.text().encode()
        keyserver = self.keyserver_edit.text().encode()
        use_proxy = self.use_proxy.isChecked()
        proxy_host = self.proxy_host_edit.text().encode()
        proxy_port = self.proxy_port_edit.text().encode()

        # Open the verifier dialog
        d = VerifierDialog(self.c, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
        d.success.connect(self.verified)
        d.exec_()

    def cancel_clicked(self):
        self.close()

    def verified(self):
        # Update the keylist values
        self.keylist.fingerprint = self.fingerprint_edit.text().encode()
        self.keylist.url = self.url_edit.text().encode()
        self.keylist.sig_url = self.keylist.url + b'.sig'
        self.keylist.keyserver = self.keyserver_edit.text().encode()
        self.keylist.use_proxy = self.use_proxy.isChecked()
        self.keylist.proxy_host = self.proxy_host_edit.text().encode()
        self.keylist.proxy_port = self.proxy_port_edit.text().encode()

        # Add the keylist, if necessary
        if self.new_keylist:
            self.c.log("KeylistDialog", "verifier_success", "adding keylist")
            self.c.settings.keylists.append(self.keylist)

        # Save settings
        self.c.settings.save()

        self.saved.emit(self.keylist)
        self.close()


class VerifierDialog(QtWidgets.QDialog):
    success = QtCore.pyqtSignal()

    def __init__(self, common, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        super(VerifierDialog, self).__init__()
        self.c = common

        self.setWindowTitle('Verifying Keylist')
        self.setWindowIcon(self.c.icon)

        # Label
        self.label = QtWidgets.QLabel("Verifying keylist")

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)

        # Timer to update the UI
        self.update_ui_timer = QtCore.QTimer()
        self.update_ui_timer.timeout.connect(self.update_ui)
        self.update_ui_timer.start(500) # 0.5 seconds

        # Start the verifier
        self.q = VerifierMessageQueue()
        self.verifier = Verifier(self.c, self.q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
        self.verifier.alert_error.connect(self.verifier_alert_error)
        self.verifier.success.connect(self.verifier_success)
        self.verifier.finished.connect(self.verifier_finished)
        self.verifier.start()

    def update_ui(self):
        # Process the last event in the LIFO queue, ignore the rest
        try:
            event = self.q.get(False)
            self.label.setText(event['msg'])
            self.progress_bar.setValue(event['step'])

        except queue.Empty:
            pass

    def verifier_alert_error(self, msg, details=''):
        self.c.alert(msg, details, QtWidgets.QMessageBox.Warning)

    def verifier_success(self):
        self.success.emit()

    def verifier_finished(self):
        self.close()
