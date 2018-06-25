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

from .endpoint import Endpoint, RefresherMessageQueue
from .endpoint_dialog import EndpointDialog


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

        self.c.log("EndpointWidget", "__init__")

        # Authority Key user ID
        uid = self.c.gpg.get_uid(self.endpoint.fingerprint)
        uid_label = QtWidgets.QLabel(uid)
        uid_label.setMinimumSize(350, 20)
        uid_label.setMaximumSize(350, 20)
        uid_label.setStyleSheet(self.c.css['EndpointWidget uid_label'])

        # Status
        if self.endpoint.syncing:
            status_text = "Syncing now..."
            status_css = self.c.css['EndpointWidget status_label']
        else:
            if self.endpoint.error:
                status_text = self.endpoint.error
                status_css = self.c.css['EndpointWidget status_label_error']
            elif self.endpoint.warning:
                status_text = self.endpoint.warning
                status_css = self.c.css['EndpointWidget status_label_warning']
            else:
                if self.endpoint.last_synced:
                    status = self.endpoint.last_synced.strftime("%B %d, %I:%M %p")
                else:
                    status = "Never"
                status_text = "Last synced: {}".format(status)
                status_css = self.c.css['EndpointWidget status_label']
        self.status_label = QtWidgets.QLabel(status_text)
        self.status_label.setStyleSheet(status_css)
        self.status_label.setMinimumSize(350, 20)
        self.status_label.setMaximumSize(350, 20)

        # Sync progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimumSize(240, 20)
        self.progress_bar.setMaximumSize(240, 20)
        self.progress_bar.hide()

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
        self.cancel_sync_button = QtWidgets.QPushButton("Cancel Sync")
        self.cancel_sync_button.clicked.connect(self.cancel_sync_clicked)
        self.cancel_sync_button.setStyleSheet(self.c.css['EndpointWidget button'])
        self.cancel_sync_button.setMinimumHeight(20)

        if self.endpoint.syncing:
            sync_button.hide()
            edit_button.hide()
            delete_button.hide()
        else:
            self.cancel_sync_button.hide()

        # Layout
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSpacing(3)
        hlayout.addWidget(self.status_label)
        hlayout.addWidget(self.progress_bar)
        hlayout.addStretch()
        hlayout.addWidget(sync_button)
        hlayout.addWidget(edit_button)
        hlayout.addWidget(delete_button)
        hlayout.addWidget(self.cancel_sync_button)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(5)
        layout.addWidget(uid_label)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        # Size
        self.setMinimumSize(350, 50)
        self.setMaximumSize(350, 50)

        # Update timer
        self.update_ui_timer = QtCore.QTimer()
        self.update_ui_timer.timeout.connect(self.update_ui)
        self.update_ui_timer.start(100) # 0.1 seconds

    def sync_clicked(self):
        self.c.log("EndpointWidget", "sync_clicked")
        self.endpoint.start_syncing(force=True)
        self.refresh.emit()

    def cancel_sync_clicked(self):
        self.c.log("EndpointWidget", "cancel_sync_clicked")
        self.cancel_sync_button.setText("Canceling...")
        self.cancel_sync_button.setEnabled(False)
        self.endpoint.refresher.cancel_early()

    def edit_clicked(self):
        self.c.log("EndpointWidget", "edit_clicked")
        d = EndpointDialog(self.c, endpoint=self.endpoint)
        d.saved.connect(self.refresh.emit)
        d.exec_()

    def delete_clicked(self):
        self.c.log("EndpointWidget", "delete_clicked")
        uid = self.c.gpg.get_uid(self.endpoint.fingerprint)
        alert_text = "Are you sure you want to delete this endpoint?<br><br><b>{}</b>".format(uid)
        reply = self.c.alert(alert_text, icon=QtWidgets.QMessageBox.Critical, question=True)
        if reply == 0:
            # Delete
            self.c.settings.endpoints.remove(self.endpoint)
            self.c.settings.save()
            self.refresh.emit()

    def update_ui(self):
        # Only need to update the UI if the endpoint is syncing
        if self.endpoint.syncing:
            # Process the last event in the LIFO queue, ignore the rest
            try:
                event = self.endpoint.q.get(False)
                if event['status'] == RefresherMessageQueue.STATUS_IN_PROGRESS:
                    self.status_label.hide()
                    self.progress_bar.show()
                    self.progress_bar.setRange(0, event['total_keys'])
                    self.progress_bar.setValue(event['current_key'])

            except queue.Empty:
                pass
