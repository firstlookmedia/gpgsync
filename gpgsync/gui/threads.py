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
from PyQt5 import QtCore, QtWidgets
from ..keylist import Keylist, ValidatorMessageQueue, RefresherMessageQueue


class ValidatorThread(QtCore.QThread):
    alert_error = QtCore.pyqtSignal(str, str)
    success = QtCore.pyqtSignal()

    def __init__(self, common, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        super(ValidatorThread, self).__init__()
        self.c = common

        # Make a keylist
        self.keylist = Keylist(self.c)
        self.keylist.fingerprint = fingerprint
        self.keylist.url = url
        self.keylist.keyserver = keyserver
        self.keylist.use_proxy = use_proxy
        self.keylist.proxy_host = proxy_host
        self.keylist.proxy_port = proxy_port
        self.keylist.q = ValidatorMessageQueue()

    def finish_with_failure(self):
        self.finished.emit()

    def run(self):
        self.c.log("ValidatorThread", "run", "starting keylist validator thread")

        result = Keylist.validate(self.c, self.keylist)

        if result['type'] == "success":
            self.success.emit()
        elif result['type'] == "error":
            self.alert_error.emit(result['message'], str(result['exception']))


class RefresherThread(QtCore.QThread):
    finished = QtCore.pyqtSignal()

    def __init__(self, common, keylist, force=False):
        super(RefresherThread, self).__init__()
        self.c = common
        self.c.log("Refresher", "__init__")

        self.keylist = keylist
        self.force = force

        self.keylist.q = RefresherMessageQueue()
        self.cancel_q = queue.Queue()

    def cancel_early(self):
        self.cancel_q.put(True)
        self.quit()

    def finish_with_failure(self, err, reset_last_checked=True):
        self.error.emit(self.e, err, reset_last_checked)

    def finish_with_cancel(self):
        self.finish_with_failure("Canceled")

    def log(self, func, message):
        self.c.log("Refresher", func, message)

    def run(self):
        self.c.log("RefresherThread", "run", "starting keylist refresher thread")

        # Return early if the keylist is already syncing
        if self.keylist.syncing:
            return
        self.keylist.syncing = True

        result = Keylist.refresh(self.c, self.cancel_q, self.keylist, force=self.force)

        if result['type'] == "success":
            self.c.log("RefresherThread", "run", "refresh success")

            if len(result['data']['invalid_fingerprints']) == 0 and len(result['data']['notfound_fingerprints']) == 0:
                warning = False
            else:
                warnings = []
                if len(result['data']['invalid_fingerprints']) > 0:
                    warning.append('Invalid fingerprints: {}'.format(', '.join([x.decode() for x in result['data']['invalid_fingerprints']])))
                if len(result['data']['notfound_fingerprints']) > 0:
                    warnings.append('Fingerprints not found: {}'.format(', '.join([x.decode() for x in result['data']['notfound_fingerprints']])))
                warning = ', '.join(warnings)

            keylist.last_checked = datetime.datetime.now()
            keylist.last_synced = datetime.datetime.now()
            keylist.warning = warning
            keylist.error = None

            self.c.settings.save()

        elif result['type'] == "error":
            self.c.log("RefresherThread", "run", "refresh error")

            if result['data']['reset_last_checked']:
                keylist.last_checked = datetime.datetime.now()
            keylist.last_failed = datetime.datetime.now()
            keylist.warning = None
            keylist.error = err

            self.c.settings.save()

        self.keylist.syncing = False
        self.finished.emit()
