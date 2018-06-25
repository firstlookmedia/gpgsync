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
import sys, platform, queue, datetime, requests
from packaging.version import parse
from PyQt5 import QtCore, QtWidgets, QtGui

from .systray import SysTray
from .settings_dialog import SettingsDialog
from .endpoint_dialog import EndpointDialog
from .endpoint_list import EndpointList


class GPGSync(QtWidgets.QMainWindow):
    def __init__(self, app, common):
        super(GPGSync, self).__init__()
        self.app = app
        self.c = common

        self.c.log("GPGSync", "__init__")

        self.system = platform.system()
        self.unconfigured_endpoint = None

        version_file = self.c.get_resource_path('version')
        self.version = parse(open(version_file).read().strip())
        self.saved_update_version = self.version

        # Initialize the window
        self.setWindowTitle('GPG Sync')
        self.setWindowIcon(self.c.icon)

        # Make sure gpg is available
        if not self.c.gpg.is_gpg_available():
            if self.system == 'Linux':
                self.c.alert('GnuPG 2.x doesn\'t seem to be installed. Install your operating system\'s gnupg2 package.')
            if self.system == 'Darwin':
                self.c.alert('GnuPG doesn\'t seem to be installed. Install <a href="https://gpgtools.org/">GPGTools</a>.')
            if self.system == 'Windows':
                self.c.alert('GnuPG doesn\'t seem to be installed. Install <a href="http://gpg4win.org/">Gpg4win</a>.')
            sys.exit()

        # Initialize endpoints
        try:
            for e in self.c.settings.endpoints:
                self.c.gpg.import_pubkey_from_disk(e.fingerprint)
                e.sync_finished.connect(self.update_ui)
        except:
            pass

        # Initialize the system tray icon
        self.systray = SysTray(self.c, self.version)
        self.systray.show_signal.connect(self.toggle_show_window)
        self.systray.sync_now_signal.connect(self.sync_all_endpoints)
        if self.system != 'Linux':
            self.checking_for_updates = False
            self.systray.check_updates_now_signal.connect(self.force_check_for_updates)
        self.systray.quit_signal.connect(self.quit)
        self.systray.show_settings_window_signal.connect(self.open_settings_window)
        self.systray.clicked_applet_signal.connect(self.clicked_applet)

        # Logo
        logo_image = QtGui.QImage(self.c.get_resource_path("gpgsync.png"))
        logo_label = QtWidgets.QLabel()
        logo_label.setPixmap(QtGui.QPixmap.fromImage(logo_image))
        logo_layout = QtWidgets.QHBoxLayout()
        logo_layout.addStretch()
        logo_layout.addWidget(logo_label)
        logo_layout.addStretch()

        # Endpoints list
        self.endpoint_list = EndpointList(self.c)
        self.endpoint_list.refresh.connect(self.update_ui)

        # Add button
        self.add_button = QtWidgets.QPushButton()
        self.add_button.clicked.connect(self.add_endpoint)
        add_button_layout = QtWidgets.QHBoxLayout()
        add_button_layout.addStretch()
        add_button_layout.addWidget(self.add_button)
        add_button_layout.addStretch()

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(logo_layout)
        layout.addWidget(self.endpoint_list)
        layout.addStretch()
        layout.addLayout(add_button_layout)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Update the UI
        self.update_ui()

        # Timed tasks intialize
        self.currently_syncing = False
        self.syncing_errors = []
        self.global_timer = QtCore.QTimer()
        self.global_timer.timeout.connect(self.run_interval_tasks)
        self.global_timer.start(60000) # 1 minute

        # Decide if window should start out shown or hidden
        if len(self.c.settings.endpoints) == 0:
            self.show()
            self.systray.set_window_show(True)
        else:
            self.hide()
            self.systray.set_window_show(False)

        # Handle application state changes
        self.first_state_change_ignored = False
        self.app.applicationStateChanged.connect(self.application_state_change)

    def run_interval_tasks(self):
        self.sync_all_endpoints(False)

        if self.system != 'Linux' and self.c.settings.run_autoupdate:
            self.check_for_updates(False)

    def application_state_change(self, state):
        # Ignore the very first state change, so window has the chance of
        # starting out hidden
        if not self.first_state_change_ignored:
            self.first_state_change_ignored = True
            return

        # If the application state is Qt::ApplicationActive, such as clicking
        # on the OS X dock icon
        # https://doc.qt.io/qt-5/qt.html#ApplicationState-enum
        if state == 4:
            self.show_main_window()

    def closeEvent(self, e):
        self.toggle_show_window()
        e.ignore()

    def toggle_show_window(self):
        if self.isHidden():
            self.show()
            self.raise_()
            self.showNormal()
            self.activateWindow()
            self.systray.set_window_show(True)
        else:
            self.hide()
            self.systray.set_window_show(False)

    def show_main_window(self):
        if self.isHidden():
            self.show()
            self.raise_()
            self.showNormal()
            self.activateWindow()
            self.systray.set_window_show(True)

    def clicked_applet(self):
        if not self.isHidden():
            self.raise_()
            self.showNormal()
            self.activateWindow()

    def open_settings_window(self):
        self.show_main_window()
        d = SettingsDialog(self.c)
        d.exec_()

    def update_ui(self):
        # Update the systray icon
        self.systray.update_icon()

        # Add button
        if len(self.c.settings.endpoints) == 0:
            self.add_button.setText("Add First GPG Sync Endpoint")
            self.add_button.setStyleSheet(self.c.css['GPGSync add_button_first'])
        else:
            self.add_button.setText("Add Endpoint")
            self.add_button.setStyleSheet(self.c.css['GPGSync add_button'])

        # Update the endpoint list
        self.endpoint_list.update_ui()

        # Set new window size
        height = len(self.c.settings.endpoints)*70 + 140
        self.setMinimumSize(420, height)
        self.setMaximumSize(420, height)

    def add_endpoint(self):
        d = EndpointDialog(self.c)
        d.saved.connect(self.add_endpoint_saved)
        d.exec_()

    def add_endpoint_saved(self, e):
        e.sync_finished.connect(self.update_ui)
        self.update_ui()

    def sync_all_endpoints(self, force=False):
        self.c.log("GPGSync", "sync_all_endpoints", "force={}".format(force))

        for e in self.c.settings.endpoints:
            e.start_syncing(force)
        self.update_ui()

    def check_for_updates(self, force=False):
        self.c.log("GPGSync", "check_for_updates", "force={}".format(force))

        one_day = 60*60*24 # One day
        run_update = False
        if self.c.settings.last_update_check is None:
            run_update = True
        elif (datetime.datetime.now() - self.c.settings.last_update_check).total_seconds() >= one_day:
            run_update = True
        elif force:
            run_update = True

        if run_update:
            if self.checking_for_updates:
                return

            self.checking_for_updates = True

            try:
                url = 'https://api.github.com/repos/firstlookmedia/gpgsync/releases/latest'

                self.c.log("GPGSync", "check_for_updates", "loading {}".format(url))
                if self.c.settings.automatic_update_use_proxy:
                    socks5_address = 'socks5://{}:{}'.format(self.c.settings.automatic_update_proxy_host.decode(), self.c.settings.automatic_update_proxy_port.decode())

                    proxies = {
                      'https': socks5_address,
                      'http': socks5_address
                    }

                    r = self.c.requests_get(url, proxies=proxies)
                else:
                    r = self.c.requests_get(url)

                release = r.json()
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
                self.c.log("GPGSync", "check_for_updates", "exception making http request: {}".format(e))
                self.checking_for_updates = False
                return

            if release and 'tag_name' in release:
                latest_version = parse(release['tag_name'])
                self.c.log("GPGSync", "check_for_updates", "latest version = {}".format(latest_version))

                if self.version < latest_version:
                    if self.saved_update_version < latest_version or force:
                        self.show_main_window()

                        self.c.update_alert(self.version, latest_version, release['html_url'])
                        self.saved_update_version = latest_version
                elif self.version >= latest_version and force:
                    self.show_main_window()
                    self.c.alert('No updates available.<br><br><span style="font-weight:normal;">Version {} is the latest version.</span>'.format(latest_version))
                self.c.settings.last_update_check_err = False
            elif release and 'tag_name' not in release:
                if not self.c.settings.last_update_check_err or force:
                    self.show_main_window()
                    details = ''
                    for key, val in release.items():
                        details += '{}: {}\n\n'.format(key, val)

                    self.c.alert('Error checking for updates.', details)
                self.c.settings.last_update_check_err = True

            self.c.settings.last_update_check = datetime.datetime.now()
            self.c.settings.save()
            self.checking_for_updates = False

    def force_check_for_updates(self):
        self.check_for_updates(True)

    def configure_autoupdate(self, state):
        if state:
            self.force_check_for_updates()

    def shutdown(self):
        self.c.log("GPGSync", "shutdown")

    def quit(self):
        self.c.log("GPGSync", "quit")
        self.app.quit()
