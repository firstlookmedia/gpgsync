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
import sys
from PyQt5 import QtCore, QtWidgets

from .gui_common import GuiCommon
from .main_window import MainWindow


class Application(QtWidgets.QApplication):
    def __init__(self, os):
        if os == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)


def main(common):
    # Create the Qt app
    app = Application(common.os)

    # Attach the GuiCommon object to Common
    common.gui = GuiCommon(common)

    # Now create the main window
    main_window = MainWindow(app, common)

    # Clean up when app quits
    def shutdown():
        main_window.shutdown()
    app.aboutToQuit.connect(shutdown)

    sys.exit(app.exec_())
