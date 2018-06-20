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
import os
import sys
import platform
from PyQt5 import QtCore, QtWidgets

from .gpgsync import GPGSync
from .common import Common


class Application(QtWidgets.QApplication):
    def __init__(self):
        if platform.system() == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)


def main():
    # https://stackoverflow.com/questions/15157502/requests-library-missing-file-after-cx-freeze
    if getattr(sys, 'frozen', False):
        os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.path.dirname(sys.executable), 'cacert.pem')

    debug = False
    if '--debug' in sys.argv:
        debug = True

    app = Application()
    common = Common(debug)
    gui = GPGSync(app, common)

    # Clean up when app quits
    def shutdown():
        gui.shutdown()
    app.aboutToQuit.connect(shutdown)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
