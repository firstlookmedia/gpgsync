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
from PySide2 import QtCore, QtWidgets, QtGui

# macOS only
if platform.system() == 'Darwin':
    from Foundation import NSUserDefaults


class GuiCommon(object):
    """
    Shared functionality across the GUI
    """
    def __init__(self, common):
        self.c = common

        # Preload icons
        self.icon = QtGui.QIcon(self.c.get_resource_path('gpgsync.png'))
        if self.c.os == 'Darwin':
            # Detect dark mode in macOS Mojova
            # See: https://stackoverflow.com/a/54701363
            if NSUserDefaults.standardUserDefaults().stringForKey_('AppleInterfaceStyle') == 'Dark':
                self.systray_icon = QtGui.QIcon(self.c.get_resource_path('gpgsync-bw-dark.png'))
                self.systray_syncing_icon = QtGui.QIcon(self.c.get_resource_path('syncing-bw-dark.png'))
            else:
                self.systray_icon = QtGui.QIcon(self.c.get_resource_path('gpgsync-bw-light.png'))
                self.systray_syncing_icon = QtGui.QIcon(self.c.get_resource_path('syncing-bw-light.png'))
        else:
            self.systray_icon = QtGui.QIcon(self.c.get_resource_path('gpgsync.png'))
            self.systray_syncing_icon = QtGui.QIcon(self.c.get_resource_path('syncing.png'))

        # Stylesheets
        self.css = {
            'MainWindow add_button': """
                QPushButton {
                    font-weight: normal;
                }
                """,

            'MainWindow add_button_first': """
                QPushButton {
                    font-weight: bold;
                }
                """,

            'KeylistDialog advanced_button': """
                QPushButton {
                    text-decoration: underline;
                    color: #225dbf;
                }
                """,

            'KeylistWidget uid_label': """
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                }
                """,

            'KeylistWidget status_label': """
                QLabel {
                    font-size: 11px;
                    font-style: italic;
                    color: #666666;
                }
                """,

            'KeylistWidget status_label_error': """
                QLabel {
                    font-size: 11px;
                    font-style: italic;
                    color: #cc0000;
                }
                """,

            'KeylistWidget status_label_warning': """
                QLabel {
                    font-size: 11px;
                    font-style: italic;
                    color: #cc8400;
                }
                """,

            'KeylistWidget button': """
                QPushButton {
                    font-size: 11px;
                }
                """
        }

    def alert(self, msg, details=None, icon=QtWidgets.QMessageBox.Warning, question=False):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle('GPG Sync')
        d.setText(msg)
        d.setWindowIcon(self.icon)

        if details != None and details != '':
            d.setDetailedText(details)

        if question:
            yes_button = d.addButton("Yes", QtWidgets.QMessageBox.YesRole)
            cancel_button = d.addButton("Cancel", QtWidgets.QMessageBox.NoRole)
            d.setDefaultButton(cancel_button)

        d.setIcon(icon)
        return d.exec_()

    def update_alert(self, curr_version, latest_version, url):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle('GPG Sync')
        d.setText('GPG Sync v{} is now available.<span style="font-weight:normal;">' \
                  '<br><br>You are currently running v{}. Click Update to' \
                  ' download the latest version </span>'.format(latest_version, curr_version))

        d.addButton(QtWidgets.QPushButton('Cancel'), QtWidgets.QMessageBox.NoRole)
        d.addButton(QtWidgets.QPushButton('Update'), QtWidgets.QMessageBox.YesRole)

        d.setIconPixmap(QtGui.QPixmap(self.c.get_resource_path('gpgsync.png')))
        res = d.exec_()

        if res == 1:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))
