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

from .endpoint import Endpoint


class EndpointList(QtWidgets.QWidget):
    refresh = QtCore.pyqtSignal()

    def __init__(self, common):
        super(EndpointList, self).__init__()
        self.c = common

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        self.update_ui()

    def update_ui(self):
        # Delete all widgets from the layout
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        # Add new endpoint widgets
        for e in self.c.settings.endpoints:
            widget = EndpointWidget(self.c, e)
            widget.refresh.connect(self.refresh.emit)
            self.layout.addWidget(widget)

        self.adjustSize()


class EndpointWidget(QtWidgets.QWidget):
    refresh = QtCore.pyqtSignal()

    def __init__(self, common, endpoint):
        super(EndpointWidget, self).__init__()
        self.c = common
        self.endpoint = endpoint

        # Authority Key user ID
        uid = self.c.gpg.get_uid(self.endpoint.fingerprint)
        uid_label = QtWidgets.QLabel(uid)
        uid_label.setMinimumSize(350, 20)
        uid_label.setMaximumSize(350, 20)
        uid_label.setStyleSheet(self.c.css['EndpointWidget uid_label'])

        # Last synced date
        if self.endpoint.last_synced:
            last_synced = self.endpoint.last_synced.strftime("%B %d, %I:%M %p")
        else:
            last_synced = 'Never'
        last_synced_label = QtWidgets.QLabel("Last synced: {}".format(last_synced))
        last_synced_label.setMinimumSize(350, 20)
        last_synced_label.setMaximumSize(350, 20)
        last_synced_label.setStyleSheet(self.c.css['EndpointWidget last_synced_label'])

        # Buttons
        sync_button = QtWidgets.QPushButton("Sync Now")
        sync_button.clicked.connect(self.sync_clicked)
        sync_button.setStyleSheet(self.c.css['EndpointWidget button'])
        sync_button.setMinimumHeight(20)
        edit_button = QtWidgets.QPushButton("Edit")
        edit_button.clicked.connect(self.edit_clicked)
        edit_button.setStyleSheet(self.c.css['EndpointWidget button'])
        edit_button.setMinimumHeight(20)
        delete_button = QtWidgets.QPushButton("Delete")
        delete_button.clicked.connect(self.delete_clicked)
        delete_button.setStyleSheet(self.c.css['EndpointWidget button'])
        delete_button.setMinimumHeight(20)

        # Layout
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSpacing(3)
        hlayout.addWidget(last_synced_label)
        hlayout.addStretch()
        hlayout.addWidget(sync_button)
        hlayout.addWidget(edit_button)
        hlayout.addWidget(delete_button)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(5)
        layout.addWidget(uid_label)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        # Size
        self.setMinimumSize(350, 50)
        self.setMaximumSize(350, 50)

    def sync_clicked(self):
        pass

    def edit_clicked(self):
        pass

    def delete_clicked(self):
        uid = self.c.gpg.get_uid(self.endpoint.fingerprint)
        alert_text = "Are you sure you want to delete this endpoint?<br><br><b>{}</b>".format(uid)
        reply = self.c.alert(alert_text, icon=QtWidgets.QMessageBox.Critical, question=True)
        if reply == 0:
            # Delete
            self.c.settings.endpoints.remove(self.endpoint)
            self.c.settings.save()
            self.refresh.emit()
