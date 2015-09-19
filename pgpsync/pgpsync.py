# -*- coding: utf-8 -*-
import sys, platform, queue
from urllib.parse import urlparse
from PyQt5 import QtCore, QtWidgets

from . import common

from .gnupg import *
from .settings import Settings

from .endpoint_selection import EndpointSelection
from .edit_endpoint import EditEndpoint
from .endpoint import Endpoint, URLDownloadError, InvalidFingerprints, FingerprintsListNotSigned
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

        # Initialize the system tray icon
        self.systray = SysTray()
        self.systray.quit_signal.connect(self.app.quit)
        self.systray.show_signal.connect(self.toggle_show_window)

        # Endpoint selection GUI
        self.endpoint_selection = EndpointSelection(self.gpg)
        self.endpoint_selection.refresh(self.settings.endpoints)
        endpoint_selection_wrapper = QtWidgets.QWidget()
        endpoint_selection_wrapper.setMinimumWidth(300)
        endpoint_selection_wrapper.setLayout(self.endpoint_selection)

        self.endpoint_selection.add_endpoint_signal.connect(self.add_endpoint)
        self.endpoint_selection.endpoint_list.itemClicked.connect(self.endpoint_clicked)

        # Edit endpoint GUI
        self.edit_endpoint = EditEndpoint()
        self.edit_endpoint_wrapper = QtWidgets.QWidget()
        self.edit_endpoint_wrapper.setMinimumWidth(400)
        self.edit_endpoint_wrapper.setLayout(self.edit_endpoint)
        self.edit_endpoint_wrapper.hide() # starts out hidden

        self.edit_endpoint.save_signal.connect(self.save_endpoint)
        self.edit_endpoint.delete_signal.connect(self.delete_endpoint)

        # Layout
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(endpoint_selection_wrapper)
        layout.addWidget(self.edit_endpoint_wrapper)
        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Check for status bar messages from other threads
        self.status_q = MessageQueue()
        self.status_bar_timer = QtCore.QTimer()
        self.status_bar_timer.timeout.connect(self.status_bar_update)
        self.status_bar_timer.start(500)

        # Decide if window should start out shown or hidden
        if len(self.settings.endpoints) == 0:
            self.show()
        else:
            self.hide()

    def closeEvent(self, e):
        self.toggle_show_window()
        e.ignore()

    def toggle_show_window(self):
        if self.isHidden():
            self.show()
        else:
            self.hide()

    def status_bar_update(self):
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
                self.status_bar.showMessage(event['msg'], event['timeout'])
            elif event['type'] == 'clear':
                self.status_bar.clearMessage()

    def edit_endpoint_alert_error(self, msg, icon=QtWidgets.QMessageBox.Warning):
        common.alert(msg, icon)

        self.status_bar.hide_loading()
        self.endpoint_selection.setEnabled(True)
        self.edit_endpoint_wrapper.setEnabled(True)

    def edit_endpoint_save(self, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        # Save the settings
        self.settings.endpoints[self.current_endpoint].update(fingerprint=fingerprint,
            url=url, keyserver=keyserver, use_proxy=use_proxy,
            proxy_host=proxy_host, proxy_port=proxy_port)
        self.settings.save()

        # Unselect endpoint
        self.endpoint_selection.endpoint_list.setCurrentItem(None)
        self.edit_endpoint_wrapper.hide()
        self.current_endpoint = None

        # Refresh the display
        self.status_bar.hide_loading()
        self.endpoint_selection.setEnabled(True)
        self.edit_endpoint_wrapper.setEnabled(True)

        self.endpoint_selection.refresh(self.settings.endpoints)

    def add_endpoint(self):
        e = Endpoint()
        self.settings.endpoints.append(e)
        self.endpoint_selection.refresh(self.settings.endpoints)

        # Click on the newest endpoint
        count = self.endpoint_selection.endpoint_list.count()
        item = self.endpoint_selection.endpoint_list.item(count-1)
        self.endpoint_selection.endpoint_list.setCurrentItem(item)
        self.endpoint_selection.endpoint_list.itemClicked.emit(item)

    def save_endpoint(self):
        class Verifier(QtCore.QThread):
            alert_error = QtCore.pyqtSignal(str)
            success = QtCore.pyqtSignal(bytes, bytes, bytes, bool, bytes, bytes)

            def __init__(self, gpg, q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
                super(Verifier, self).__init__()
                self.gpg = gpg
                self.q = q
                self.fingerprint = fingerprint
                self.url = url
                self.keyserver = keyserver
                self.use_proxy = use_proxy
                self.proxy_host = proxy_host
                self.proxy_port = proxy_port

            def finish_with_failure(self):
                self.q.add_message(type='clear')
                self.finished.emit()

            def run(self):
                # Make an endpoint
                e = Endpoint()
                e.update(self.fingerprint, self.url, self.keyserver, self.use_proxy, self.proxy_host, self.proxy_port)

                # Test fingerprint and keyserver, and that the key isn't revoked or expired
                success = False
                try:
                    self.q.add_message('Downloading {} from keyserver {}'.format(common.fp_to_keyid(self.fingerprint).decode(), self.keyserver.decode()))
                    e.fetch_public_key(self.gpg)
                except InvalidFingerprint:
                    self.alert_error.emit('Invalid signing key fingerprint.')
                except InvalidKeyserver:
                    self.alert_error.emit('Invalid keyserver.')
                except NotFoundOnKeyserver:
                    self.alert_error.emit('Signing key is not found on keyserver. Upload signing key and try again.')
                except NotFoundInKeyring:
                    self.alert_error.emit('Signing key is not found in keyring. Something went wrong.')
                except RevokedKey:
                    self.alert_error.emit('The signing key is revoked.')
                except ExpiredKey:
                    self.alert_error.emit('The signing key is expired.')
                else:
                    success = True

                if not success:
                    return self.finish_with_failure()

                # Make sure URL is in the right format
                success = False
                o = urlparse(self.url)
                if (o.scheme != b'http' and o.scheme != b'https') or o.netloc == '':
                    self.alert_error.emit('URL is invalid.')
                else:
                    success = True

                if not success:
                    return self.finish_with_failure()

                # Test loading URL
                success = False
                try:
                    self.q.add_message('Testing downloading URL {}'.format(self.url.decode()))
                    msg_bytes = e.fetch_url()
                except URLDownloadError as e:
                    self.alert_error.emit('URL failed to download: {}'.format(e))
                else:
                    success = True

                if not success:
                    return self.finish_with_failure()

                # After downloading URL, test that it's signed by signing key
                success = False
                try:
                    self.q.add_message('Verifying signature')
                    e.verify_fingerprints_sig(self.gpg, msg_bytes)
                except VerificationError:
                    self.alert_error.emit('Signature does not verify.')
                except BadSignature:
                    self.alert_error.emit('Bad signature.')
                except RevokedKey:
                    self.alert_error.emit('The signing key is revoked.')
                except SignedWithWrongKey:
                    self.alert_error.emit('Valid signature, but signed with wrong signing key.')
                else:
                    success = True

                if not success:
                    return self.finish_with_failure()

                # Test that it's a list of fingerprints
                success = False
                try:
                    self.q.add_message('Validating fingerprint list')
                    e.get_fingerprint_list(msg_bytes)
                except InvalidFingerprints as e:
                    self.alert_error.emit('URL contains invalid fingerprints: {}'.format(e))
                except FingerprintsListNotSigned:
                    self.alert_error.emit('Fingerprints list is not signed.')
                else:
                    success = True

                if not success:
                    return self.finish_with_failure()

                self.q.add_message('Endpoint saved', timeout=4000)
                self.success.emit(fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
                self.finished.emit()

        # Get values for endpoint
        fingerprint = common.clean_fp(self.edit_endpoint.fingerprint_edit.text().encode())
        url         = self.edit_endpoint.url_edit.text().encode()
        keyserver   = self.edit_endpoint.keyserver_edit.text().encode()
        use_proxy   = self.edit_endpoint.use_proxy.checkState() == QtCore.Qt.Checked
        proxy_host  = self.edit_endpoint.proxy_host_edit.text().encode()
        proxy_port  = self.edit_endpoint.proxy_port_edit.text().encode()

        # Show loading graphic, and disable all input until it's finished Verifying
        self.status_bar.show_loading()
        self.endpoint_selection.setEnabled(False)
        self.edit_endpoint_wrapper.setEnabled(False)

        # Run the verifier inside a new thread
        self.verifier = Verifier(self.gpg, self.status_q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
        self.verifier.alert_error.connect(self.edit_endpoint_alert_error)
        self.verifier.success.connect(self.edit_endpoint_save)
        self.verifier.start()

    def delete_endpoint(self):
        self.edit_endpoint_wrapper.hide()
        self.settings.endpoints.remove(self.settings.endpoints[self.current_endpoint])
        self.endpoint_selection.refresh(self.settings.endpoints)
        self.current_endpoint = None

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

def main():
    app = Application()
    gui = PGPSync(app)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
