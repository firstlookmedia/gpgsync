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
import datetime
from PyQt5 import QtCore, QtWidgets
from ..keylist import Keylist, ValidatorMessageQueue, RefresherMessageQueue


class AuthorityKeyValidatorThread(QtCore.QThread):
    """
    In order to display the UID of the authority key in the UI, we need to first
    fetch the authority key from a keyserver. But in order to do that, we need
    to first download the keylist, to learn what keyserver we should be using.
    """
    alert_error = QtCore.pyqtSignal(str, str)
    success = QtCore.pyqtSignal()

    def __init__(self, common, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        super(AuthorityKeyValidatorThread, self).__init__()
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
        self.c.log("AuthorityKeyValidatorThread", "run", "starting authority key validator thread")

        # Download keylist URI
        result = self.keylist.refresh_keylist_uri()
        if result['type'] == 'success':
            msg_bytes = result['data']
        else:
            self.c.log("ValidatorThread", "run", "Error: {} {}".format(result['message'], result['exception']))
            self.alert_error.emit(result['message'], result['exception'])
            return

        # Run validate_format, so we can parse out the keyserver to use
        try:
            common.log("Keylist", "refresh", "Validating keylist format")
            self.keylist.validate_format(msg_bytes)
        except:
            pass

        # Validate the authority key -- basically just to fetch it from the keyserver
        result = self.keylist.validate_authority_key()
        if result['type'] == 'success':
            self.success.emit()
        else:
            self.c.log("ValidatorThread", "run", "Error: {} {}".format(result['message'], result['exception']))
            self.alert_error.emit(result['message'], result['exception'])


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

        self.is_finished = False

    def cancel_early(self):
        self.cancel_q.put(True)
        self.quit()

    def log(self, func, message):
        self.c.log("Refresher", func, message)

    def run(self):
        self.c.log("RefresherThread", "run", "starting keylist refresher thread")

        # Return early if the keylist is already syncing
        if self.keylist.syncing:
            return
        self.keylist.syncing = True

        result = Keylist.refresh(self.c, self.cancel_q, self.keylist, force=self.force)
        self.keylist.interpret_result(result)

        self.keylist.syncing = False
        self.is_finished = True
        self.c.log("RefresherThread", "run", "thread finished")
        self.finished.emit()
