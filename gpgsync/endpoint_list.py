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
    def __init__(self, common):
        super(EndpointList, self).__init__()
        self.c = common

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.update_ui()

    def update_ui(self):
        # Delete all widgets from the layout
        # https://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)

        # Add new endpoint widgets
        for e in self.c.settings.endpoints:
            self.layout.addWidget(EndpointWidget(self.c, e))

        self.adjustSize()


class EndpointWidget(QtWidgets.QWidget):
    def __init__(self, common, endpoint):
        super(EndpointWidget, self).__init__()
        self.c = common

        # Display the fingerprint for now
        label = QtWidgets.QLabel(endpoint.fingerprint.decode())

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        self.setLayout(layout)
