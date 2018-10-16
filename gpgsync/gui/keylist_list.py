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
import queue
import time
from PyQt5 import QtCore, QtWidgets, QtGui

from .keylist_dialog import KeylistDialog
from .threads import RefresherThread
from ..keylist import Keylist, RefresherMessageQueue


class KeylistList(QtWidgets.QWidget):
    refresh = QtCore.pyqtSignal()

    def __init__(self, common):
        super(KeylistList, self).__init__()
        self.c = common
        self.c.log('KeylistList', '__init__')

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(10)
        self.setLayout(self.layout)

        self.update_ui()

    def update_ui(self):
        self.c.log('KeylistList', 'update_ui')

        # Add new keylist widgets
        for keylist in self.c.settings.keylists:
            widget = KeylistWidget(self.c, keylist)
            widget.refresh.connect(self.refresh.emit)
            self.layout.addWidget(widget)

        self.adjustSize()


class KeylistWidget(QtWidgets.QWidget):
    refresh = QtCore.pyqtSignal()

    def __init__(self, common, keylist):
        super(KeylistWidget, self).__init__()
        self.c = common
        self.c.log('KeylistWidget', '__init__')
        self.keylist = keylist

        self.c.log("KeylistWidget", "__init__")

        # Authority Key user ID
        uid = self.c.gpg.get_uid(self.keylist.fingerprint)
        uid_label = QtWidgets.QLabel(uid)
        uid_label.setMinimumSize(440, 30)
        uid_label.setMaximumSize(440, 30)
        uid_label.setStyleSheet(self.c.gui.css['KeylistWidget uid_label'])

        # Status
        self.status_label = QtWidgets.QLabel()
        self.status_label.setMinimumSize(440, 20)
        self.status_label.setMaximumSize(440, 20)

        # Sync progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimumSize(290, 20)
        self.progress_bar.setMaximumSize(290, 20)
        self.progress_bar.hide()

        # Buttons
        self.info_button = QtWidgets.QPushButton("Info")
        self.info_button.clicked.connect(self.details_clicked)
        self.info_button.setStyleSheet(self.c.gui.css['KeylistWidget button'])
        self.sync_button = QtWidgets.QPushButton("Sync Now")
        self.sync_button.clicked.connect(self.sync_clicked)
        self.sync_button.setStyleSheet(self.c.gui.css['KeylistWidget button'])
        self.edit_button = QtWidgets.QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_clicked)
        self.edit_button.setStyleSheet(self.c.gui.css['KeylistWidget button'])
        self.delete_button = QtWidgets.QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_clicked)
        self.delete_button.setStyleSheet(self.c.gui.css['KeylistWidget button'])
        self.cancel_sync_button = QtWidgets.QPushButton("Cancel Sync")
        self.cancel_sync_button.clicked.connect(self.cancel_sync_clicked)
        self.cancel_sync_button.setStyleSheet(self.c.gui.css['KeylistWidget button'])

        # Layout
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSpacing(4)
        hlayout.addWidget(self.status_label)
        hlayout.addWidget(self.progress_bar)
        hlayout.addStretch()
        hlayout.addWidget(self.info_button)
        hlayout.addWidget(self.sync_button)
        hlayout.addWidget(self.edit_button)
        hlayout.addWidget(self.delete_button)
        hlayout.addWidget(self.cancel_sync_button)
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(uid_label)
        layout.addLayout(hlayout)
        self.setLayout(layout)

        # Size
        self.setMinimumSize(440, 70)
        self.setMaximumSize(440, 70)

        # Update timer
        self.update_ui_timer = QtCore.QTimer()
        self.update_ui_timer.timeout.connect(self.update_ui)
        self.update_ui_timer.start(100) # 0.1 seconds

    def details_clicked(self):
        self.c.log("KeylistWidget", "details_clicked")
        if self.keylist.error:
            self.c.gui.alert("Sync error:\n\n{}".format(self.keylist.error), icon=QtWidgets.QMessageBox.Critical)
        elif self.keylist.warning:
            self.c.gui.alert("Sync warning:\n\n{}".format(self.keylist.warning), icon=QtWidgets.QMessageBox.Warning)

    def sync_clicked(self):
        self.c.log("KeylistWidget", "sync_clicked")

        self.keylist.refresher = RefresherThread(self.c, self.keylist, force=True)
        self.keylist.refresher.finished.connect(self.refresh.emit)
        self.keylist.refresher.start()
        time.sleep(0.1) # wait for thread to start

        self.refresh.emit()

    def cancel_sync_clicked(self):
        self.c.log("KeylistWidget", "cancel_sync_clicked")
        self.cancel_sync_button.setText("Canceling...")
        self.cancel_sync_button.setEnabled(False)
        self.keylist.refresher.cancel_early()

    def edit_clicked(self):
        self.c.log("KeylistWidget", "edit_clicked")
        d = KeylistDialog(self.c, keylist=self.keylist)
        d.saved.connect(self.refresh.emit)
        d.exec_()

    def delete_clicked(self):
        self.c.log("KeylistWidget", "delete_clicked")
        uid = self.c.gpg.get_uid(self.keylist.fingerprint)
        alert_text = "Are you sure you want to delete this keylist?<br><br><b>{}</b>".format(uid)
        reply = self.c.gui.alert(alert_text, icon=QtWidgets.QMessageBox.Critical, question=True)
        if reply == 0:
            # Delete
            self.c.settings.keylists.remove(self.keylist)
            self.c.settings.save()
            self.refresh.emit()

    def update_ui(self):
        # Only need to update the UI if the keylist is syncing
        if self.keylist.syncing:
            self.cancel_sync_button.show()
            self.info_button.hide()
            self.sync_button.hide()
            self.edit_button.hide()
            self.delete_button.hide()

            self.status_label.setText("Syncing now...")
            self.status_label.setStyleSheet(self.c.gui.css['KeylistWidget status_label'])

            # Process the last event in the LIFO queue, ignore the rest
            try:
                event = self.keylist.q.get(False)
                if event['status'] == RefresherMessageQueue.STATUS_IN_PROGRESS:
                    self.status_label.hide()
                    self.progress_bar.show()
                    self.progress_bar.setRange(0, event['total_keys'])
                    self.progress_bar.setValue(event['current_key'])

            except queue.Empty:
                pass
        else:
            # Not syncing
            self.status_label.show()
            self.progress_bar.hide()

            self.cancel_sync_button.hide()
            self.info_button.show()
            self.sync_button.show()
            self.edit_button.show()
            self.delete_button.show()

            if self.keylist.error or self.keylist.warning:
                self.info_button.show()
            else:
                self.info_button.hide()

            # Update status label and css
            if self.keylist.error:
                status_text = 'Error syncing'
                status_css = self.c.gui.css['KeylistWidget status_label_error']
            else:
                if self.keylist.last_synced:
                    status = self.keylist.last_synced.strftime("%B %d, %I:%M %p")
                else:
                    status = "Never"
                status_text = "Synced {}".format(status)
                if self.keylist.warning:
                    status_css = self.c.gui.css['KeylistWidget status_label_warning']
                else:
                    status_css = self.c.gui.css['KeylistWidget status_label']
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet(status_css)
