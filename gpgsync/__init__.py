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
import os, sys, platform, queue, datetime, requests, time
from packaging.version import parse
from urllib.parse import urlparse
from PyQt5 import QtCore, QtWidgets

from . import common

from .gnupg import GnuPG
from .settings import Settings

from .endpoint_selection import EndpointSelection
from .edit_endpoint import EditEndpoint
from .endpoint import Endpoint, Verifier, Refresher, URLDownloadError, ProxyURLDownloadError, InvalidFingerprints
from .buttons import Buttons
from .status_bar import StatusBar, MessageQueue
from .systray import SysTray
from .settings_window import SettingsWindow

class Application(QtWidgets.QApplication):
    def __init__(self):
        if platform.system() == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)

class GPGSync(QtWidgets.QMainWindow):
    def __init__(self, app, debug=False):
        super(GPGSync, self).__init__()
        self.app = app
        self.debug = debug
        self.system = platform.system()
        self.setWindowTitle('GPG Sync')
        self.setWindowIcon(common.get_icon())
        version_file = common.get_resource_path('version')
        self.version = parse(open(version_file).read().strip())
        self.saved_update_version = self.version
        self.unconfigured_endpoint = None

        self.threads = []

        # Load settings
        self.settings = Settings()

        # Initialize gpg
        self.gpg = GnuPG(appdata_path=self.settings.get_appdata_path(), debug=debug)
        if not self.gpg.is_gpg_available():
            if self.system == 'Linux':
                common.alert('GnuPG 2.x doesn\'t seem to be installed. Install your operating system\'s gnupg2 package.')
            if self.system == 'Darwin':
                common.alert('GnuPG doesn\'t seem to be installed. Install <a href="https://gpgtools.org/">GPGTools</a>.')
            if self.system == 'Windows':
                common.alert('GnuPG doesn\'t seem to be installed. Install <a href="http://gpg4win.org/">Gpg4win</a>.')
            sys.exit()

        # Initialize endpoints
        self.current_endpoint = None
        try:
            for e in self.settings.endpoints:
                if e.verified:
                    self.gpg.import_pubkey_from_disk(e.fingerprint)
                else:
                    self.unconfigured_endpoint = e
        except:
            pass

        self.settings_window = SettingsWindow(self.settings)

        # Initialize the system tray icon
        self.systray = SysTray(self.version)
        self.systray.show_signal.connect(self.toggle_show_window)
        self.systray.sync_now_signal.connect(self.sync_all_endpoints)
        if self.system != 'Linux':
            self.checking_for_updates = False
            self.systray.check_updates_now_signal.connect(self.force_check_for_updates)
        self.systray.quit_signal.connect(self.quit)
        self.systray.show_settings_window_signal.connect(self.open_settings_window)
        self.systray.clicked_applet_signal.connect(self.clicked_applet)

        # Endpoint selection GUI
        self.endpoint_selection = EndpointSelection(self.gpg)
        self.endpoint_selection.load_endpoints(self.settings.endpoints)
        endpoint_selection_wrapper = QtWidgets.QWidget()
        endpoint_selection_wrapper.setMinimumWidth(300)
        endpoint_selection_wrapper.setLayout(self.endpoint_selection)

        self.endpoint_selection.add_endpoint_signal.connect(self.add_endpoint)
        self.endpoint_selection.endpoint_list.itemClicked.connect(self.endpoint_clicked)

        if self.unconfigured_endpoint is not None:
            self.endpoint_selection.add_btn.setEnabled(False)

        # Edit endpoint GUI
        self.edit_endpoint = EditEndpoint()
        self.edit_endpoint_wrapper = QtWidgets.QWidget()
        self.edit_endpoint_wrapper.setMinimumWidth(400)
        self.edit_endpoint_wrapper.setLayout(self.edit_endpoint)
        self.edit_endpoint_wrapper.hide() # starts out hidden

        self.edit_endpoint.save_signal.connect(self.save_endpoint)
        self.edit_endpoint.delete_signal.connect(self.delete_endpoint)

        # Buttons
        self.buttons = Buttons(self.settings)
        self.buttons.sync_now_signal.connect(self.sync_all_endpoints)
        self.buttons.autoupdate_signal.connect(self.configure_autoupdate)
        self.buttons.quit_signal.connect(self.quit)
        self.sync_msg = None

        # Layout
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(endpoint_selection_wrapper)
        hlayout.addWidget(self.edit_endpoint_wrapper)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(hlayout)
        layout.addLayout(self.buttons)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Check for status bar messages from other threads
        # Also, reload endpoint display
        self.status_q = MessageQueue()
        self.update_ui_timer = QtCore.QTimer()
        self.update_ui_timer.timeout.connect(self.update_ui)
        self.update_ui_timer.start(500) # 0.5 seconds

        # Timed tasks intialize
        self.currently_syncing = False
        self.syncing_errors = []

        self.global_timer = QtCore.QTimer()
        self.global_timer.timeout.connect(self.run_interval_tasks)
        self.global_timer.start(60000) # 1 minute

        # Decide if window should start out shown or hidden
        if len(self.settings.endpoints) == 0:
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

        if self.system != 'Linux' and self.settings.run_autoupdate:
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

    def update_ui(self):
        # Print events, and update status bar
        events = []
        done = False
        while not done:
            try:
                ev = self.status_q.get(False)
                events.append(ev)
            except queue.Empty:
                done = True

        for event in events:
            if event['type'] == 'update':
                print(event['msg'])
                if not self.isHidden():
                    self.status_bar.showMessage(event['msg'], event['timeout'])
            elif event['type'] == 'clear':
                if not self.isHidden():
                    self.status_bar.clearMessage()

        # Ignore the rest of the UI if window is hidden
        if self.isHidden():
            return

        # Endpoint display
        self.endpoint_selection.reload_endpoints()

        # Sync message
        if(self.sync_msg):
            self.buttons.update_sync_label(self.sync_msg)
        else:
            self.buttons.update_sync_label()

    def edit_endpoint_alert_error(self, msg, details='', icon=QtWidgets.QMessageBox.Warning):
        common.alert(msg, details, icon)
        self.toggle_input(True)

    def edit_endpoint_save(self, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        # Save the settings
        self.settings.endpoints[self.current_endpoint].verified = True
        self.settings.endpoints[self.current_endpoint].fingerprint = fingerprint
        self.settings.endpoints[self.current_endpoint].url = url
        self.settings.endpoints[self.current_endpoint].sig_url = url + b'.sig'
        self.settings.endpoints[self.current_endpoint].keyserver = keyserver
        self.settings.endpoints[self.current_endpoint].use_proxy = use_proxy
        self.settings.endpoints[self.current_endpoint].proxy_host = proxy_host
        self.settings.endpoints[self.current_endpoint].proxy_port = proxy_port
        self.settings.save()
        self.unconfigured_endpoint = None

        # Refresh the display
        self.toggle_input(True)
        self.endpoint_selection.reload_endpoint(self.settings.endpoints[self.current_endpoint])

        # Unselect endpoint
        self.endpoint_selection.endpoint_list.setCurrentItem(None)
        self.edit_endpoint_wrapper.hide()
        self.current_endpoint = None

        self.sync_all_endpoints(True)

    def open_settings_window(self):
        self.show_main_window()
        self.settings_window.show()

    def add_endpoint(self):
        e = Endpoint()
        self.settings.endpoints.append(e)
        self.endpoint_selection.add_endpoint(e)
        self.unconfigured_endpoint = e
        self.endpoint_selection.add_btn.setEnabled(False)

        # Click on the newest endpoint
        count = self.endpoint_selection.endpoint_list.count()
        item = self.endpoint_selection.endpoint_list.item(count-1)
        self.endpoint_selection.endpoint_list.setCurrentItem(item)
        self.endpoint_selection.endpoint_list.itemClicked.emit(item)

    def save_endpoint(self):
        # Get values for endpoint
        fingerprint = common.clean_fp(self.edit_endpoint.fingerprint_edit.text().strip().encode())
        url         = self.edit_endpoint.url_edit.text().strip().encode()
        keyserver   = self.edit_endpoint.keyserver_edit.text().strip().encode()
        use_proxy   = self.edit_endpoint.use_proxy.checkState() == QtCore.Qt.Checked
        proxy_host  = self.edit_endpoint.proxy_host_edit.text().strip().encode()
        proxy_port  = self.edit_endpoint.proxy_port_edit.text().strip().encode()

        # Show loading graphic, and disable all input until it's finished Verifying
        self.toggle_input(False)

        # Run the verifier inside a new thread
        self.verifier = Verifier(self.debug, self.gpg, self.status_q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
        self.threads.append(self.verifier)
        print("[GPGSync] save_endpoint, adding Verifier thread ({} threads right now)".format(len(self.threads)))
        self.verifier.alert_error.connect(self.edit_endpoint_alert_error)
        self.verifier.success.connect(self.edit_endpoint_save)
        self.verifier.finished.connect(self.clean_threads)
        self.verifier.start()

    def delete_endpoint(self):
        self.edit_endpoint_wrapper.hide()
        if self.settings.endpoints[self.current_endpoint] is self.unconfigured_endpoint:
            self.unconfigured_endpoint = None
            self.endpoint_selection.add_btn.setEnabled(True)
        self.endpoint_selection.delete_endpoint(self.settings.endpoints[self.current_endpoint])
        self.settings.endpoints.remove(self.settings.endpoints[self.current_endpoint])
        self.current_endpoint = None
        self.settings.save()

    def endpoint_clicked(self, item):
        try:
            i = self.settings.endpoints.index(item.endpoint)
        except ValueError:
            print('ERROR: Invalid endpoint')
            return

        # Clicking on an already-selected endpoint unselects it
        if i == self.current_endpoint:
            self.edit_endpoint_wrapper.hide()
            self.endpoint_selection.endpoint_list.setCurrentItem(None)
            self.current_endpoint = None

        # Select new endpoint
        else:
            self.current_endpoint = i
            self.edit_endpoint.set_endpoint(item.endpoint)
            self.edit_endpoint_wrapper.show()

    def refresher_finished(self):
        self.clean_threads()

        if len(self.waiting_refreshers) > 0:
            r = self.waiting_refreshers.pop()
            self.active_refreshers.append(r)
            r.start()
        else:
            self.status_q.add_message('Syncing complete.', timeout=4000)
            self.currently_syncing = False
            self.toggle_input(True)

    def refresher_success(self, e, invalid_fingerprints, notfound_fingerprints):
        if len(invalid_fingerprints) == 0 and len(notfound_fingerprints) == 0:
            warning = False
        else:
            warnings = []
            if len(invalid_fingerprints) > 0:
                warning.append('Invalid fingerprints {}'.format(invalid_fingerprints))
            if len(notfound_fingerprints) > 0:
                warnings.append('Not found fingerprints {}'.format(notfound_fingerprints))
            warning = ', '.join(warnings)

        e.last_checked = datetime.datetime.now()
        e.last_synced = datetime.datetime.now()
        e.warning = warning
        e.error = None

        self.endpoint_selection.reload_endpoint(e)
        self.settings.save()

    def refresher_error(self, e, err, reset_last_checked=True):
        self.syncing_errors.append(e)
        if reset_last_checked:
            e.last_checked = datetime.datetime.now()
        e.last_failed = datetime.datetime.now()
        e.warning = None
        e.error = err

        self.endpoint_selection.reload_endpoint(e)
        self.settings.save()

    def clean_threads(self):
        if self.debug:
            print("[GPGSync] clean_threads ({} threads right now)".format(len(self.threads)))

        # Remove all threads from self.threads that are finished
        done_removing = False
        while not done_removing:
            for t in self.threads:
                if t.isFinished():
                    self.threads.remove(t)
                    if self.debug:
                        print("[GPGSync] removing a thread".format(len(self.threads)))
                    break
            done_removing = True

    def sync_all_endpoints(self, force=False):
        # Skip if a sync is currently in progress
        if self.currently_syncing:
            return

        self.currently_syncing = True
        self.syncing_errors = []

        # Make a refresher for each endpoint
        self.waiting_refreshers = []
        self.active_refreshers = []
        for e in self.settings.endpoints:
            if e.verified:
                refresher = Refresher(self.debug, self.gpg, self.settings.update_interval_hours, self.status_q, e, force)
                self.threads.append(refresher)
                print("[GPGSync] sync_all_endpoints, adding Refresher thread ({} threads right now)".format(len(self.threads)))
                refresher.finished.connect(self.refresher_finished)
                refresher.success.connect(self.refresher_success)
                refresher.error.connect(self.refresher_error)
                self.waiting_refreshers.append(refresher)

        # Start the first refresher thread
        if len(self.waiting_refreshers) > 0:
            r = self.waiting_refreshers.pop()
            self.active_refreshers.append(r)
            r.start()

            sync_string = "Syncing: {} {}".format(self.gpg.get_uid(r.e.fingerprint), common.fp_to_keyid(r.e.fingerprint).decode())
            print(sync_string)
            self.toggle_input(False, sync_string)

    def toggle_input(self, enabled=False, sync_msg=None):
        # Show/hide loading graphic
        if enabled:
            self.status_bar.hide_loading()
            self.systray.setIcon(common.icon)
        else:
            self.status_bar.show_loading()
            self.systray.setIcon(common.get_syncing_icon())

        # Disable/enable all input
        if self.unconfigured_endpoint is not None:
            self.endpoint_selection.add_btn.setEnabled(False)
            self.endpoint_selection.endpoint_list.setEnabled(enabled)
        else:
            self.endpoint_selection.setEnabled(enabled)
        self.edit_endpoint_wrapper.setEnabled(enabled)
        self.buttons.sync_now_btn.setEnabled(enabled)
        self.systray.refresh_act.setEnabled(enabled)

        # Next sync check message
        if enabled:
            self.sync_msg = None
        else:
            self.sync_msg = sync_msg

        if len(self.syncing_errors) > 0:
            self.systray.setIcon(common.get_error_icon())

    def check_for_updates(self, force=False):
        one_day = 60*60*24 # One day
        run_update = False
        if self.settings.last_update_check is None:
            run_update = True
        elif (datetime.datetime.now() - self.settings.last_update_check).total_seconds() >= one_day:
            run_update = True
        elif force:
            run_update = True

        if run_update:
            if self.checking_for_updates:
                return

            self.checking_for_updates = True

            try:
                url = 'https://api.github.com/repos/firstlookmedia/gpgsync/releases/latest'

                if self.settings.automatic_update_use_proxy:
                    socks5_address = 'socks5://{}:{}'.format(self.settings.automatic_update_proxy_host.decode(), self.settings.automatic_update_proxy_port.decode())

                    proxies = {
                      'https': socks5_address,
                      'http': socks5_address
                    }

                    r = common.requests_get(url, proxies=proxies)
                else:
                    r = common.requests_get(url)

                release = r.json()
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
                self.checking_for_updates = False
                return

            if release and 'tag_name' in release:
                latest_version = parse(release['tag_name'])

                if self.version < latest_version:
                    if self.saved_update_version < latest_version or force:
                        self.show_main_window()

                        common.alert('A new version of GPG Sync is available.<span style="font-weight:normal;"><br><br>Current: {}<br>Latest: &nbsp;&nbsp;{}<br><br>Please download the <a href="{}">latest</a> version.</span>'.format(self.version, latest_version, release['html_url']))
                        self.saved_update_version = latest_version
                elif self.version == latest_version and force:
                    self.show_main_window()
                    common.alert('No updates available.')
                self.settings.last_update_check_err = False
            elif release and 'tag_name' not in release:
                if not self.settings.last_update_check_err or force:
                    self.show_main_window()
                    details = ''
                    for key, val in release.items():
                        details += '{}: {}\n\n'.format(key, val)

                    common.alert('Error checking for updates.', details)
                self.settings.last_update_check_err = True

            self.settings.last_update_check = datetime.datetime.now()
            self.settings.save()
            self.checking_for_updates = False

    def force_check_for_updates(self):
        self.check_for_updates(True)

    def configure_autoupdate(self, state):
        if state:
            self.force_check_for_updates()

    def quit(self):
        if self.debug:
            print("[GPGSync] quit ({} threads)".format(len(self.threads)))

        # Tell all the threads to quit
        for t in self.threads:
            if self.debug:
                print("[GPGSync] terminating thread {}".format(type(t)))

            t.terminate()
            t.wait()

        self.app.quit()

def main():
    # https://stackoverflow.com/questions/15157502/requests-library-missing-file-after-cx-freeze
    if getattr(sys, 'frozen', False):
        os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.path.dirname(sys.executable), 'cacert.pem')

    debug = False
    if '--debug' in sys.argv:
        debug = True

    app = Application()
    gui = GPGSync(app, debug)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
