import sys, platform
from PyQt4 import QtCore, QtGui

from gnupg import GnuPG, InvalidFingerprint, InvalidKeyserver, NotFoundOnKeyserver, NotFoundInKeyring, RevokedKey, ExpiredKey
from settings import Settings
import common

from endpoint_selection import EndpointSelection
from edit_endpoint import EditEndpoint
from endpoint import Endpoint

class Application(QtGui.QApplication):
    def __init__(self):
        if platform.system() == 'Linux':
            self.setAttribute(QtCore.Qt.AA_X11InitThreads, True)
        QtGui.QApplication.__init__(self, sys.argv)

class PGPSync(QtGui.QWidget):
    def __init__(self, app):
        super(PGPSync, self).__init__()
        self.app = app
        self.system = platform.system()
        self.setWindowTitle('PGP Sync')

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

        # Endpoint selection GUI
        self.endpoint_selection = EndpointSelection(self.gpg)
        self.endpoint_selection.refresh(self.settings.endpoints)
        endpoint_selection_wrapper = QtGui.QWidget()
        endpoint_selection_wrapper.setMinimumWidth(300)
        endpoint_selection_wrapper.setLayout(self.endpoint_selection)

        self.endpoint_selection.add_endpoint_signal.connect(self.add_endpoint)
        self.endpoint_selection.endpoint_list.itemClicked.connect(self.endpoint_clicked)

        # Edit endpoint GUI
        self.edit_endpoint = EditEndpoint()
        self.edit_endpoint_wrapper = QtGui.QWidget()
        self.edit_endpoint_wrapper.setMinimumWidth(400)
        self.edit_endpoint_wrapper.setLayout(self.edit_endpoint)
        self.edit_endpoint_wrapper.hide() # starts out hidden

        self.edit_endpoint.save_signal.connect(self.save_endpoint)
        self.edit_endpoint.delete_signal.connect(self.delete_endpoint)

        # Layout
        layout = QtGui.QHBoxLayout()
        layout.addWidget(endpoint_selection_wrapper)
        layout.addWidget(self.edit_endpoint_wrapper)
        self.setLayout(layout)
        self.show()

    def edit_endpoint_alert_error(self, msg, icon=QtGui.QMessageBox.Warning):
        self.edit_endpoint.hide_loading_animation()
        common.alert(msg, icon)

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
        self.edit_endpoint.hide_loading_animation()
        self.endpoint_selection.refresh(self.settings.endpoints)

    def add_endpoint(self):
        e = Endpoint()
        print e.fingerprint
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
            success = QtCore.pyqtSignal(str, str, str, bool, str, str)

            def __init__(self, gpg, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
                super(Verifier, self).__init__()
                self.gpg = gpg
                self.fingerprint = fingerprint
                self.url = url
                self.keyserver = keyserver
                self.use_proxy = use_proxy
                self.proxy_host = proxy_host
                self.proxy_port = proxy_port

            def run(self):
                # Test fingerprint and keyserver
                recv_key_success = False
                try:
                    self.gpg.recv_key(self.keyserver, self.fingerprint)
                except InvalidFingerprint:
                    self.alert_error.emit('Invalid signing key fingerprint.')
                except InvalidKeyserver:
                    self.alert_error.emit('Invalid keyserver.')
                except NotFoundOnKeyserver:
                    self.alert_error.emit('Signing key is not found on keyserver. Upload signing key and try again.')
                except NotFoundInKeyring:
                    self.alert_error.emit('Signing key is not found in keyring. Something went wrong.')
                else:
                    recv_key_success = True

                if not recv_key_success:
                    self.finished.emit()
                    return

                # Fingerprint is valid, and we have retrived it from the keyserver
                # Check if the key is revoked or expired
                pubkey_success = False
                try:
                    self.gpg.test_key(self.fingerprint)
                except RevokedKey:
                    self.alert_error.emit('The signing key is revoked.')
                except ExpiredKey:
                    self.alert_error.emit('The signing key is expired.')
                else:
                    pubkey_success = True

                if not pubkey_success:
                    self.finished.emit()
                    return

                # TODO: Make sure URL is in the right format

                # TODO: If use_proxy, test loading URL over proxy

                # TODO: If not use_proxy, test loading URL not over proxy

                # TODO: After downloading URL, test that it's signed by signing key

                # TODO: After verifying sig, test that it's a list of fingerprints
                
                self.success.emit(fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
                self.finished.emit()

        # Get values for endpoint
        fingerprint = common.clean_fp(str(self.edit_endpoint.fingerprint_edit.text()))
        url         = str(self.edit_endpoint.url_edit.text())
        keyserver   = str(self.edit_endpoint.keyserver_edit.text())
        use_proxy   = self.edit_endpoint.use_proxy.checkState() == QtCore.Qt.Checked
        proxy_host  = str(self.edit_endpoint.proxy_host_edit.text())
        proxy_port  = str(self.edit_endpoint.proxy_port_edit.text())

        # Run the verifier inside a new thread
        self.edit_endpoint.show_loading_animation()
        self.verifier = Verifier(self.gpg, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port)
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
            print 'ERROR: Invalid endpoint'
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
