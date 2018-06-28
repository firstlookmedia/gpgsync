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
import datetime
import os
import sys
import re
import platform
import inspect
import requests
import socket
from PyQt5 import QtCore, QtWidgets, QtGui

from .gnupg import GnuPG
from .settings import Settings


class Common(object):
    """
    The Common class is a singleton of shared functionality throughout the app
    """
    def __init__(self, debug):
        self.debug = debug

        # Load settings
        self.settings = Settings(self)

        # Initialize GnuPG
        self.gpg = GnuPG(self, appdata_path=self.settings.get_appdata_path())

        # Preload icons
        self.icon = QtGui.QIcon(self.get_resource_path('gpgsync.png'))
        if platform.system() == 'Darwin':
            self.systray_icon = QtGui.QIcon(self.get_resource_path('gpgsync-bw.png'))
            self.systray_syncing_icon = QtGui.QIcon(self.get_resource_path('syncing-bw.png'))
        else:
            self.systray_icon = QtGui.QIcon(self.get_resource_path('gpgsync.png'))
            self.systray_syncing_icon = QtGui.QIcon(self.get_resource_path('syncing.png'))

        # Stylesheets
        self.css = {
            'GPGSync add_button': """
                QPushButton {
                    font-weight: normal;
                }
                """,

            'GPGSync add_button_first': """
                QPushButton {
                    font-weight: bold;
                }
                """,

            'EndpointDialog sig_url': """
                QLabel {
                    font-style: italic;
                    color: #666666;
                    font-size: 11px;
                }
                """,

            'EndpointDialog advanced_button': """
                QPushButton {
                    text-decoration: underline;
                    color: #225dbf;
                }
                """,

            'EndpointWidget uid_label': """
                QLabel {
                    font-weight: bold;
                    font-size: 14px;
                }
                """,

            'EndpointWidget status_label': """
                QLabel {
                    font-size: 11px;
                    font-style: italic;
                    color: #666666;
                }
                """,

            'EndpointWidget status_label_error': """
                QLabel {
                    font-size: 11px;
                    font-style: italic;
                    color: #cc0000;
                }
                """,

            'EndpointWidget status_label_warning': """
                QLabel {
                    font-size: 11px;
                    font-style: italic;
                    color: #cc8400;
                }
                """,

            'EndpointWidget button': """
                QPushButton {
                    font-size: 11px;
                }
                """
        }

    def log(self, module, func, msg=''):
        if self.debug:
            final_msg = "[{}] {}".format(module, func)
            if msg:
                final_msg = "{}: {}".format(final_msg, msg)
            print(final_msg)

    def alert(self, msg, details='', icon=QtWidgets.QMessageBox.Warning, question=False):
        d = QtWidgets.QMessageBox()
        d.setWindowTitle('GPG Sync')
        d.setText(msg)
        d.setWindowIcon(self.icon)

        if details:
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

        d.setIconPixmap(QtGui.QPixmap(self.get_resource_path('gpgsync.png')))
        res = d.exec_()

        if res == 1:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    def clean_fp(self, fp):
        if type(fp) == bytes:
            return fp.strip().replace(b' ', b'').upper()
        else:
            return fp.strip().replace(' ', '').upper().encode()

    def valid_fp(self, fp):
        return re.match(b'^[A-F\d]{40}$', self.clean_fp(fp))

    def fp_to_keyid(self, fp):
        return '0x{}'.format(self.clean_fp(fp)[-16:].decode()).encode()

    def clean_keyserver(self, keyserver):
        if b'://' not in keyserver:
            return b'hkp://' + keyserver
        return keyserver

    def get_resource_path(self, filename):
        if getattr(sys, 'gpgsync_dev', False):
            # Look for resources directory relative to python file
            prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), 'share')

        # Check if app is "frozen"
        # https://pythonhosted.org/PyInstaller/#run-time-information
        elif getattr(sys, 'frozen', False):
            prefix = os.path.join(os.path.dirname(sys.executable), 'share')

        elif platform.system() == 'Linux':
            prefix = os.path.join(sys.prefix, 'share/gpgsync')

        resource_path = os.path.join(prefix, filename)
        return resource_path

    def requests_get(self, url, proxies=None):
        # When creating an OSX app bundle, the requests module can't seem to find
        # the location of cacerts.pem. Here's a hack to let it know where it is.
        # https://stackoverflow.com/questions/17158529/fixing-ssl-certificate-error-in-exe-compiled-with-py2exe-or-pyinstaller
        if getattr(sys, 'frozen', False):
            if platform.system() == 'Darwin':
                verify = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Resources/certifi/cacert.pem')
            elif platform.system() == 'Windows':
                verify = os.path.join(os.path.dirname(sys.executable), 'certifi/cacert.pem')
            else:
                verify = None
            return requests.get(url, proxies=proxies, verify=verify)
        else:
            return requests.get(url, proxies=proxies)

    def serialize_settings(self, o):
        if isinstance(o, bytes):
            return o.decode()
        if isinstance(o, datetime.datetime):
            return o.isoformat()

    def internet_available(self):
        try:
            host = socket.gethostbyname("www.example.com")
            s = socket.create_connection((host, 80), 2)
            return True
        except:
            pass

        return False
