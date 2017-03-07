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
import re, time, datetime
from PyQt5 import QtCore, QtWidgets, QtGui

from . import common

class EndpointWidget(QtWidgets.QWidget):
    def __init__(self, item, endpoint, gpg):
        super(EndpointWidget, self).__init__()
        self.item = item
        self.e = endpoint
        self.gpg = gpg

        # If the endpoint isn't configured yet
        self.not_configured_label = QtWidgets.QLabel('Not configured')
        self.not_configured_label.setStyleSheet("QLabel { color: #CC0000; }")

        # User id and keyid of signing key
        self.uid_label = QtWidgets.QLabel()
        self.uid_label.setStyleSheet("QLabel { font-weight: bold; }")
        if self.e.uid_label:
            self.uid_label.setText(self.e.uid_label.decode())
        self.keyid_label = QtWidgets.QLabel()
        self.keyid_label.setStyleSheet("QLabel { font-style: italic; color: #333333; }")

        # Last updated
        self.last_checked_label = QtWidgets.QLabel()
        self.last_checked_label.setStyleSheet("QLabel { color: #333333; }")

        # Warning and error
        self.warning_label = QtWidgets.QLabel()
        self.warning_label.setStyleSheet("QLabel { color: #C36900; }")
        self.error_label = QtWidgets.QLabel()
        self.error_label.setStyleSheet("QLabel { color: #CC0000; }")

        # Widget layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.not_configured_label)
        layout.addWidget(self.uid_label)
        layout.addWidget(self.keyid_label)
        layout.addWidget(self.last_checked_label)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.error_label)
        self.setLayout(layout)

        self.update()

    def update(self):
        # If the endpoint isn't configured yet
        if not common.valid_fp(self.e.fingerprint):
            self.not_configured_label.show()
            self.uid_label.hide()
            self.keyid_label.hide()
            self.last_checked_label.hide()
            self.warning_label.hide()
            self.error_label.hide()
            self.item.setSizeHint(QtCore.QSize(0, 80))
            return

        # The endpoint is configured
        self.not_configured_label.hide()
        self.uid_label.show()
        self.keyid_label.show()
        self.last_checked_label.show()

        # User id and keyid of signing key
        uid = self.gpg.get_uid(self.e.fingerprint)
        self.uid_label.setText(uid)
        keyid = common.fp_to_keyid(self.e.fingerprint).decode()
        self.keyid_label.setText(keyid)

        # Last updated
        if self.e.last_checked:
            if self.e.error:
                diff = datetime.datetime.now() - self.e.last_failed
            else:
                diff = datetime.datetime.now() - self.e.last_synced
            s = diff.seconds
            hours = s // 3600
            s = s - (hours * 3600)
            minutes = s // 60
            seconds = s - (minutes * 60)

            if hours > 0:
                last_checked = '{} hours ago'.format(hours)
            elif minutes > 0:
                last_checked = '{} minutes ago'.format(minutes)
            else:
                last_checked = '{} seconds ago'.format(seconds)
        else:
            last_checked = 'never'

        if self.e.error:
            self.last_checked_label.setText('Last attempted: {}'.format(last_checked))
        else:
            self.last_checked_label.setText('Last synced: {}'.format(last_checked))

        # Warning and error
        if self.e.warning:
            self.warning_label.setText('Warning: {}'.format(self.e.warning))
            self.warning_label.show()
        else:
            self.warning_label.hide()
        if self.e.error:
            self.error_label.setText('Error: {}'.format(self.e.error))
            self.error_label.show()
        else:
            self.error_label.hide()

        # Size
        if self.e.warning and self.e.error:
            self.item.setSizeHint(QtCore.QSize(0, 120))
        elif self.e.warning and not self.e.error or self.e.error and not self.e.warning:
            self.item.setSizeHint(QtCore.QSize(0, 100))
        else:
            self.item.setSizeHint(QtCore.QSize(0, 80))

class EndpointList(QtWidgets.QListWidget):
    def __init__(self, gpg):
        super(EndpointList, self).__init__()
        self.gpg = gpg
        self.setStyleSheet("""
            QListWidget::item { background: rgb(255, 255, 255);  }
            QListWidget::item:selected { background: rgb(153, 204, 255); }
        """)

    def iter_all_items(self):
        for i in range(self.count()):
            yield self.item(i)

    def add_endpoint(self, e):
        item = QtWidgets.QListWidgetItem()
        item.endpoint = e
        self.addItem(item)
        self.setItemWidget(item, EndpointWidget(item, e, self.gpg))

    def load_endpoints(self, endpoints):
        self.clear()
        for e in endpoints:
            self.add_endpoint(e)

    def reload_endpoint(self, endpoint):
        for item in self.iter_all_items():
            if item.endpoint == endpoint:
                self.itemWidget(item).update()

    def reload_endpoints(self):
        for item in self.iter_all_items():
            self.itemWidget(item).update()

    def delete_endpoint(self, endpoint):
        for item in self.iter_all_items():
            if item:
                if item.endpoint == endpoint:
                    self.removeItemWidget(item)
                    self.takeItem(self.row(item))

class EndpointSelection(QtWidgets.QVBoxLayout):
    add_endpoint_signal = QtCore.pyqtSignal()

    def __init__(self, gpg):
        super(EndpointSelection, self).__init__()
        self.gpg = gpg

        self.endpoint_list = EndpointList(gpg)

        self.add_btn = QtWidgets.QPushButton("Add Endpoint")
        self.add_btn.clicked.connect(self.add_new_endpoint)

        self.addWidget(self.endpoint_list)
        self.addWidget(self.add_btn)

    def add_new_endpoint(self):
        self.add_endpoint_signal.emit()

    def add_endpoint(self, e):
        self.endpoint_list.add_endpoint(e)

    def load_endpoints(self, e):
        self.endpoint_list.load_endpoints(e)

    def reload_endpoint(self, e):
        self.endpoint_list.reload_endpoint(e)

    def reload_endpoints(self):
        self.endpoint_list.reload_endpoints()

    def delete_endpoint(self, e):
        self.endpoint_list.delete_endpoint(e)

    def setEnabled(self, enabled):
        self.endpoint_list.setEnabled(enabled)
        self.add_btn.setEnabled(enabled)
