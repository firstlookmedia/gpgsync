# -*- coding: utf-8 -*-
import re, time, datetime
from PyQt5 import QtCore, QtWidgets, QtGui

from . import common

class EndpointWidget(QtWidgets.QWidget):
    def __init__(self, e, gpg):
        super(EndpointWidget, self).__init__()

        # If the endpoint isn't configured yet
        if not common.valid_fp(e.fingerprint):
            not_configured_label = QtWidgets.QLabel('Not configured')
            not_configured_label.setStyleSheet("QLabel { color: #CC0000; }")

            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(not_configured_label)
            self.setLayout(layout)
            return

        # User id of signing key
        uid = gpg.get_uid(e.fingerprint)
        uid_label = QtWidgets.QLabel(uid)
        uid_label.setStyleSheet("QLabel { font-weight: bold; }")

        # Keyid of singing key
        keyid = common.fp_to_keyid(e.fingerprint).decode()
        keyid_label = QtWidgets.QLabel(keyid)
        keyid_label.setStyleSheet("QLabel { font-style: italic; color: #666666; }")

        # Last updated
        if e.last_checked:
            diff = datetime.datetime.now() - e.last_checked
            s = diff.seconds
            hours = s // 3600
            s = s - (hours * 3600)
            minutes = s // 60
            seconds = s - (minutes * 60)

            if hours > 0:
                last_checked = '{} hours ago'.format(hours)
            elif minutes > 0:
                last_checked = '{} minutes ago'.format(seconds)
            else:
                last_checked = '{} seconds ago'.format(seconds)
        else:
            last_checked = 'never'
        last_checked_label = QtWidgets.QLabel('Last updated: {}'.format(last_checked))
        last_checked_label.setStyleSheet("QLabel { color: #666666; }")

        # Warning and error
        if e.warning:
            warning_label = QtWidgets.QLabel('Warning: {}'.format(e.warning))
            warning_label.setStyleSheet("QLabel { color: #C36900; }")
        if e.error:
            error_label = QtWidgets.QLabel('Error: {}'.format(e.error))
            error_label.setStyleSheet("QLabel { color: #CC0000; }")

        # Widget layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(uid_label)
        layout.addWidget(keyid_label)
        layout.addWidget(last_checked_label)
        if e.warning:
            layout.addWidget(warning_label)
        if e.error:
            layout.addWidget(error_label)
        self.setLayout(layout)

class EndpointList(QtWidgets.QListWidget):
    def __init__(self, gpg):
        super(EndpointList, self).__init__()
        self.gpg = gpg

    def add_endpoint(self, e):
        item = QtWidgets.QListWidgetItem()
        item.endpoint = e
        if e.warning and e.error:
            item.setSizeHint(QtCore.QSize(0, 120))
        elif e.warning and not e.error or e.error and not e.warning:
            item.setSizeHint(QtCore.QSize(0, 100))
        else:
            item.setSizeHint(QtCore.QSize(0, 80))
        self.addItem(item)
        self.setItemWidget(item, EndpointWidget(e, self.gpg))

    def refresh(self, endpoints):
        self.clear()

        for e in endpoints:
            self.add_endpoint(e)

class EndpointSelection(QtWidgets.QVBoxLayout):
    add_endpoint_signal = QtCore.pyqtSignal()

    def __init__(self, gpg):
        super(EndpointSelection, self).__init__()
        self.gpg = gpg

        self.endpoint_list = EndpointList(gpg)

        self.add_btn = QtWidgets.QPushButton("Add Endpoint")
        self.add_btn.clicked.connect(self.add_endpoint)

        self.addWidget(self.endpoint_list)
        self.addWidget(self.add_btn)

    def add_endpoint(self):
        self.add_endpoint_signal.emit()

    def refresh(self, endpoints):
        self.endpoint_list.refresh(endpoints)

    def setEnabled(self, enabled):
        self.endpoint_list.setEnabled(enabled)
        self.add_btn.setEnabled(enabled)
