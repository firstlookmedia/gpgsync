# -*- coding: utf-8 -*-
import os, sys, platform, queue, datetime, requests
from packaging.version import parse
from urllib.parse import urlparse
from PyQt5 import QtCore, QtWidgets

from . import common

from .gnupg import GnuPG
from .settings import Settings

from .endpoint_selection import EndpointSelection
from .edit_endpoint import EditEndpoint
from .endpoint import Endpoint, Verifier, Refresher, URLDownloadError, ProxyURLDownloadError, InvalidFingerprints, FingerprintsListNotSigned
from .buttons import Buttons
from .status_bar import StatusBar, MessageQueue
from .systray import SysTray

class Application(QtWidgets.QApplication):
    def __init__(self):
        if platform.system() == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtWidgets.QApplication.__init__(self, sys.argv)

class PGPSync(QtWidgets.QMainWindow):
    def __init__(self, app):
        super(PGPSync, self).__init__()
        self.app = app
        self.system = platform.system()
        self.setWindowTitle('PGP Sync')
        self.setWindowIcon(common.get_icon())
        version_file = common.get_resource_path('version')
        self.version = parse(open(version_file).read().strip())
        self.saved_update_version = self.version
        self.unconfigured_endpoint = None

        # Initialize gpg
        self.gpg = GnuPG()
        if not self.gpg.is_gpg_available():
            if self.system == 'Linux':
                common.alert('GnuPG 2.x doesn\'t seem to be installed. Install your operating system\'s gnupg2 package.')
            if self.system == 'Darwin':
                common.alert('GnuPG doesn\'t seem to be installed. Install <a href="https://gpgtools.org/">GPGTools</a>.')
            if self.system == 'Windows':
                common.alert('GnuPG doesn\'t seem to be installed. Install <a href="http://gpg4win.org/">Gpg4win</a>.')
            sys.exit()

        # Load settings
        self.settings = Settings()
        self.current_endpoint = None
        try:
            for e in self.settings.endpoints:
                if e.verified:
                    e.fetch_public_key(self.gpg)
                else:
                    self.unconfigured_endpoint = e
        except:
            pass

        # Initialize the system tray icon
        self.systray = SysTray(self.version)
        self.systray.show_signal.connect(self.toggle_show_window)
        self.systray.sync_now_signal.connect(self.sync_all_endpoints)
        if self.system != 'Linux':
            self.checking_for_updates = False
            self.systray.check_updates_now_signal.connect(self.force_check_for_updates)
        self.systray.quit_signal.connect(self.app.quit)
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
        self.buttons.quit_signal.connect(self.app.quit)
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

        # Timer to refresh endpoints
        self.currently_syncing = False
        self.syncing_errors = []
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.sync_all_endpoints)
        self.refresh_timer.start(60000) # 1 minute

        # Timer to check for automatic updates
        if self.system != 'Linux' and self.settings.run_autoupdate:
            self.check_for_updates() # Check first on start up
            self.updater_timer = QtCore.QTimer()
            self.updater_timer.timeout.connect(self.check_for_updates)
            self.updater_timer.start(86400000) # 24 hours

        # Decide if window should start out shown or hidden
        if len(self.settings.endpoints) == 0:
            self.show()
            self.systray.set_window_show(True)
        else:
            self.hide()
            self.systray.set_window_show(False)

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
        self.verifier = Verifier(self.gpg, self.status_q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
        self.verifier.alert_error.connect(self.edit_endpoint_alert_error)
        self.verifier.success.connect(self.edit_endpoint_save)
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
                refresher = Refresher(self.gpg, self.status_q, e, force)
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
        if self.checking_for_updates:
            return

        self.checking_for_updates = True

        try:
            url = 'https://api.github.com/repos/firstlookmedia/pgpsync/releases/latest'
            token = '8890473be7c382a70eadb8fbc58ffe0fea913b77'

            r = requests.get(url, headers={
                'Authorization': 'token {}'.format(token)
                })

            release = r.json()
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
            self.checking_for_updates = False
            return

        if release and 'tag_name' in release:
            latest_version = parse(release['tag_name'])

            if self.version < latest_version:
                if self.saved_update_version < latest_version or force:
                    self.show_main_window()

                    common.alert('A new version of PGP Sync is available.<span style="font-weight:normal;"><br><br>Current: {}<br>Latest: &nbsp;&nbsp;{}<br><br>Please download the <a href="{}?access_token={}">latest</a> version.</span>'.format(self.version, latest_version, release['html_url'], token))
                    self.saved_update_version = latest_version
            elif self.version == latest_version and force:
                self.show_main_window()
                common.alert('No updates available.')
        elif release and 'tag_name' not in release:
            self.show_main_window()
            details = ''
            for key, val in release.items():
                details += '{}: {}\n\n'.format(key, val)

            common.alert('Error checking for updates.', details)

        self.checking_for_updates = False

    def force_check_for_updates(self):
        self.check_for_updates(True)

    def configure_autoupdate(self, state):
        if state:
            try:
                if self.updater_timer:
                    self.force_check_for_updates()
                    self.updater_timer.start(86400000)
            except:
                self.check_for_updates() # Check first on start up
                self.updater_timer = QtCore.QTimer()
                self.updater_timer.timeout.connect(self.check_for_updates)
                self.updater_timer.start(86400000) # 24 hours
        else:
            if self.updater_timer:
                self.updater_timer.stop()

def main():
    app = Application()
    gui = PGPSync(app)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
