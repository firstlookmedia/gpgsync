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
from ..keylist import Keylist


class ValidatorThread(QtCore.QThread):
    alert_error = QtCore.pyqtSignal(str, str)
    success = QtCore.pyqtSignal()

    def __init__(self, common, q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        super(ValidatorThread, self).__init__()
        self.c = common
        self.q = q

        # Make a keylist
        self.keylist = Keylist(self.c)
        self.keylist.fingerprint = fingerprint
        self.keylist.url = url
        self.keylist.keyserver = keyserver
        self.keylist.use_proxy = use_proxy
        self.keylist.proxy_host = proxy_host
        self.keylist.proxy_port = proxy_port

    def finish_with_failure(self):
        self.finished.emit()

    def run(self):
        self.c.log("ValidatorThread", "run", "starting to keylist validator thread")
        result = Keylist.validate(self.c, self.q, self.keylist)
        if result:
            self.success.emit()
        else:
            self.alert_error.emit(result['error'], str(result['exception']))
