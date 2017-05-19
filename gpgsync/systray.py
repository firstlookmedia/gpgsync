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
import queue, platform
from PyQt5 import QtCore, QtWidgets

from . import common

class SysTray(QtWidgets.QSystemTrayIcon):
    show_signal = QtCore.pyqtSignal()
    sync_now_signal = QtCore.pyqtSignal(bool)
    check_updates_now_signal = QtCore.pyqtSignal(bool)
    show_settings_window_signal = QtCore.pyqtSignal(bool)
    quit_signal = QtCore.pyqtSignal()
    clicked_applet_signal = QtCore.pyqtSignal()

    def __init__(self, version):
        super(SysTray, self).__init__(common.get_systray_icon())
        self.show_text = 'Show GPG Sync'
        self.hide_text = 'Hide GPG Sync'

        # Menu
        self.menu = QtWidgets.QMenu()
        self.version_info = self.menu.addAction('Version {}'.format(version))
        self.version_info.setEnabled(False)
        self.show_act = self.menu.addAction(self.show_text)
        self.show_act.triggered.connect(self.clicked_show)
        self.refresh_act = self.menu.addAction('Sync endpoints')
        self.refresh_act.triggered.connect(self.clicked_refresh)
        if platform.system() != 'Linux':
            self.update_act = self.menu.addAction('Check for updates')
            self.update_act.triggered.connect(self.clicked_update_now)
        self.settings_window = self.menu.addAction('Settings...')
        self.settings_window.triggered.connect(self.clicked_settings)
        self.menu.addSeparator()
        self.quit_act = self.menu.addAction('Quit')
        self.quit_act.triggered.connect(self.clicked_quit)

        self.setContextMenu(self.menu)
        self.activated.connect(self.clicked_activated)

        # Show the systray icon
        self.show()

    def clicked_activated(self, reason):
        # Clicking the systray icon raises window in OSX
        if platform.system() == 'Darwin':
            self.clicked_applet_signal.emit()
            return

        # Clicking the systray icon shows/hides the window
        if reason == self.Trigger:
            self.clicked_show()

    def set_window_show(self, showing):
        if showing:
            self.show_act.setText(self.hide_text)
        else:
            self.show_act.setText(self.show_text)

    def clicked_show(self):
        self.show_signal.emit()

    def clicked_refresh(self):
        self.sync_now_signal.emit(True)

    def clicked_update_now(self):
        self.check_updates_now_signal.emit(True)

    def clicked_settings(self):
        self.show_settings_window_signal.emit(True)

    def clicked_quit(self):
        self.quit_signal.emit()
