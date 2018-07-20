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
import requests
import socks
import uuid
import datetime
import dateutil.parser as date_parser
import queue
from io import BytesIO
from PyQt5 import QtCore, QtWidgets

from .gnupg import *


class URLDownloadError(Exception):
    pass


class ProxyURLDownloadError(Exception):
    pass


class InvalidFingerprints(Exception):
    def __init__(self, fingerprints):
        self.fingerprints = fingerprints

    def __str__(self):
        return str([s.decode() for s in self.fingerprints])


class Endpoint(QtCore.QObject):
    fetched_public_key_signal = QtCore.pyqtSignal()
    sync_finished = QtCore.pyqtSignal()

    def __init__(self, common):
        super(Endpoint, self).__init__()
        self.c = common

        self.fingerprint = b''
        self.url = b''
        self.sig_url = b'https://.sig'
        self.keyserver = b'hkps://hkps.pool.sks-keyservers.net'
        self.use_proxy = False
        self.proxy_host = b'127.0.0.1'
        self.proxy_port = b'9050'
        self.last_checked = None
        self.last_synced = None
        self.last_failed = None
        self.error = None
        self.warning = None

        # Temporary variable for if it's in the middle of syncing
        self.syncing = False
        self.q = None

    """
    Acts as a secondary constructor to load an endpoint from settings
    """
    def load(self, e):
        self.fingerprint = str.encode(e['fingerprint'])
        self.url = str.encode(e['url'])
        self.sig_url = str.encode(e['sig_url'])
        self.keyserver = str.encode(e['keyserver'])
        self.use_proxy = e['use_proxy']
        self.proxy_host = str.encode(e['proxy_host'])
        self.proxy_port = str.encode(e['proxy_port'])
        self.last_checked = (date_parser.parse(e['last_checked']) if e['last_checked'] is not None else None)
        self.last_synced = (date_parser.parse(e['last_synced']) if e['last_synced'] is not None else None)
        self.last_failed = (date_parser.parse(e['last_failed']) if e['last_failed'] is not None else None)
        self.error = e['error']
        self.warning = e['warning']

        return self

    def serialize(self):
        tmp = {}

        for k, v in self.__dict__.items():
            if isinstance(v, bytes):
                tmp[k] = v.decode()
            elif isinstance(v, datetime.datetime):
                tmp[k] = v.isoformat()
            else:
                tmp[k] = v

        return tmp

    def fetch_public_key(self, gpg):
        # Retreive the signing key from the keyserver
        gpg.recv_key(self.keyserver, self.fingerprint, self.use_proxy, self.proxy_host, self.proxy_port)

        # Test the key for issues
        gpg.test_key(self.fingerprint)

        # Save it to disk
        gpg.export_pubkey_to_disk(self.fingerprint)

        self.fetched_public_key_signal.emit()

    def fetch_msg_url(self):
        return self.fetch_url(self.url)

    def fetch_msg_sig_url(self):
        return self.fetch_url(self.sig_url)

    def fetch_url(self, url):
        try:
            if self.use_proxy:
                socks5_address = 'socks5://{}:{}'.format(self.proxy_host.decode(), self.proxy_port.decode())

                proxies = {
                  'https': socks5_address,
                  'http': socks5_address
                }

                r = self.c.requests_get(url, proxies=proxies)
            else:
                r = self.c.requests_get(url)

            r.close()
            msg_bytes = r.content
        except (socks.ProxyConnectionError, requests.exceptions.RequestException, requests.exceptions.ConnectionError) as e:
            if self.use_proxy:
                raise ProxyURLDownloadError(e)
            else:
                raise URLDownloadError(e)

        return msg_bytes

    def verify_fingerprints_sig(self, gpg, msg_sig_bytes, msg_bytes):
        # Make sure the signature is valid
        gpg.verify(msg_sig_bytes, msg_bytes, self.fingerprint)

    def get_fingerprint_list(self, msg_bytes):
        # Convert the message content into a list of fingerprints
        fingerprints = []
        invalid_fingerprints = []
        for line in msg_bytes.split(b'\n'):
            # If there are comments in the line, remove the comments
            if b'#' in line:
                line = line.split(b'#')[0]

            # Skip blank lines
            if line.strip() == b'':
                continue

            # Test for valid fingerprints
            if self.c.valid_fp(line):
                fingerprints.append(line)
            else:
                invalid_fingerprints.append(line)

        if len(invalid_fingerprints) > 0:
            raise InvalidFingerprints(invalid_fingerprints)

        return fingerprints

    def start_syncing(self, force=False):
        if self.syncing:
            return

        self.syncing = True

        # Start the Refresher
        self.q = RefresherMessageQueue()
        self.refresher = Refresher(self.c, self.c.settings.update_interval_hours, self.q, self, force)
        self.refresher.finished.connect(self.refresher_finished)
        self.refresher.success.connect(self.refresher_success)
        self.refresher.error.connect(self.refresher_error)
        self.refresher.start()

    def refresher_finished(self):
        self.c.log("Endpoint", "refresher_finished")
        self.syncing = False
        self.sync_finished.emit()

    def refresher_success(self, e, invalid_fingerprints, notfound_fingerprints):
        self.c.log("Endpoint", "refresher_success")

        if len(invalid_fingerprints) == 0 and len(notfound_fingerprints) == 0:
            warning = False
        else:
            warnings = []
            if len(invalid_fingerprints) > 0:
                warning.append('Invalid fingerprints: {}'.format(', '.join([x.decode() for x in invalid_fingerprints])))
            if len(notfound_fingerprints) > 0:
                warnings.append('Fingerprints not found: {}'.format(', '.join([x.decode() for x in notfound_fingerprints])))
            warning = ', '.join(warnings)

        e.last_checked = datetime.datetime.now()
        e.last_synced = datetime.datetime.now()
        e.warning = warning
        e.error = None

        self.c.settings.save()

    def refresher_error(self, e, err, reset_last_checked=True):
        self.c.log("Endpoint", "refresher_error")

        if reset_last_checked:
            e.last_checked = datetime.datetime.now()
        e.last_failed = datetime.datetime.now()
        e.warning = None
        e.error = err

        self.c.settings.save()


class VerifierMessageQueue(queue.LifoQueue):
    def __init(self):
        super(VerifierMessageQueue, self).__init__()

    def add_message(self, msg, step):
        self.put({
            'msg': msg,
            'step': step
        })


class Verifier(QtCore.QThread):
    alert_error = QtCore.pyqtSignal(str, str)
    success = QtCore.pyqtSignal(bytes, bytes, bytes, bool, bytes, bytes)

    def __init__(self, common, q, fingerprint, url, keyserver, use_proxy, proxy_host, proxy_port):
        super(Verifier, self).__init__()
        self.c = common
        self.q = q
        self.fingerprint = fingerprint
        self.url = url
        self.sig_url = self.url + b'.sig'
        self.keyserver = keyserver
        self.use_proxy = use_proxy
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def finish_with_failure(self):
        self.finished.emit()

    def log(self, func, message, step=0):
        self.c.log("Verifier", func, message)
        self.q.add_message(message, step)

    def run(self):
        print("Verifying keylist with authority key {}".format(self.fingerprint.decode()))

        # Make an endpoint
        e = Endpoint(self.c)
        e.fingerprint = self.fingerprint
        e.url = self.url
        e.sig_url = self.sig_url
        e.keyserver = self.keyserver
        e.use_proxy = self.use_proxy
        e.proxy_host = self.proxy_host
        e.proxy_port = self.proxy_port

        # Test loading URL
        success = False
        try:
            self.log('run', 'Testing downloading URL {}'.format(self.url.decode()), 0)
            msg_bytes = e.fetch_msg_url()
        except ProxyURLDownloadError as e:
            self.alert_error.emit('URL failed to download: Check your internet connection and proxy settings.', str(e))
        except URLDownloadError as e:
            self.alert_error.emit('URL failed to download: Check your internet connection.', str(e))
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        # Test loading signature URL
        success = False
        try:
            self.log('run', 'Testing downloading URL {}'.format(self.sig_url.decode()), 1)
            msg_sig_bytes = e.fetch_msg_sig_url()
        except ProxyURLDownloadError as e:
            self.alert_error.emit('URL failed to download: Check your internet connection and proxy settings.', str(e))
        except URLDownloadError as e:
            self.alert_error.emit('URL failed to download: Check your internet connection.', str(e))
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        # Test fingerprint and keyserver, and that the key isn't revoked or expired
        success = False
        try:
            self.log('run', 'Downloading {} from keyserver {}'.format(self.c.fp_to_keyid(self.fingerprint).decode(), self.keyserver.decode()), 2)
            e.fetch_public_key(self.c.gpg)
        except InvalidFingerprint:
            self.alert_error.emit('Invalid signing key fingerprint.', '')
        except KeyserverError:
            self.alert_error.emit('Error with keyserver {}.'.format(self.keyserver.decode()), '')
        except NotFoundOnKeyserver:
            self.alert_error.emit('Signing key is not found on keyserver. Upload signing key and try again.', '')
        except NotFoundInKeyring:
            self.alert_error.emit('Signing key is not found in keyring. Something went wrong.', '')
        except RevokedKey:
            self.alert_error.emit('The signing key is revoked.', '')
        except ExpiredKey:
            self.alert_error.emit('The signing key is expired.', '')
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        # Make sure URL is in the right format
        success = False
        o = urlparse(self.url)
        if (o.scheme != b'http' and o.scheme != b'https') or o.netloc == '':
            self.alert_error.emit('URL is invalid.', '')
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        # After downloading URL, test that it's signed by signing key
        success = False
        try:
            self.log('run', 'Verifying signature', 3)
            e.verify_fingerprints_sig(self.c.gpg, msg_sig_bytes, msg_bytes)
        except VerificationError:
            self.alert_error.emit('Signature does not verify.', '')
        except BadSignature:
            self.alert_error.emit('Bad signature.', '')
        except RevokedKey:
            self.alert_error.emit('The signing key is revoked.', '')
        except SignedWithWrongKey:
            self.alert_error.emit('Valid signature, but signed with wrong signing key.', '')
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        # Test that it's a list of fingerprints
        success = False
        try:
            self.log('run', 'Validating fingerprint list', 4)
            e.get_fingerprint_list(msg_bytes)
        except InvalidFingerprints as e:
            self.alert_error.emit('Invalid fingerprints', str(e))
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        self.log('run', 'Endpoint saved', 5)

        self.success.emit(self.fingerprint, self.url, self.keyserver, self.use_proxy, self.proxy_host, self.proxy_port)
        self.finished.emit()


class RefresherMessageQueue(queue.LifoQueue):
    STATUS_STARTING = 0
    STATUS_IN_PROGRESS = 1

    def __init(self):
        super(RefresherMessageQueue, self).__init__()

    def add_message(self, status, total_keys=0, current_key=0):
        self.put({
            'status': status,
            'total_keys': total_keys,
            'current_key': current_key
        })


class Refresher(QtCore.QThread):
    success = QtCore.pyqtSignal(Endpoint, list, list)
    error = QtCore.pyqtSignal(Endpoint, str, bool)

    def __init__(self, common, refresh_interval, q, endpoint, force=False):
        super(Refresher, self).__init__()
        self.c = common
        self.c.log("Refresher", "__init__")

        # this should be safe to cast directly to a float since it passed the input test
        self.refresh_interval = float(refresh_interval)
        self.q = q
        self.e = endpoint
        self.force = force

        self.should_cancel = False

    def cancel_early(self):
        self.should_cancel = True
        self.quit()

    def finish_with_failure(self, err, reset_last_checked=True):
        self.error.emit(self.e, err, reset_last_checked)

    def finish_with_cancel(self):
        self.finish_with_failure("Canceled")

    def log(self, func, message):
        self.c.log("Refresher", func, message)

    def run(self):
        print("Refreshing keylist with authority key {}".format(self.e.fingerprint.decode()))

        self.q.add_message(RefresherMessageQueue.STATUS_STARTING)

        # Refresh if it's forced, if it's never been checked before,
        # or if it's been longer than the configured refresh interval
        update_interval = 60*60*(self.refresh_interval)
        run_refresher = False

        # If there is no connection - skip
        if not self.c.internet_available():
            return

        if self.force:
            print('Forcing sync')
            run_refresher = True
        elif not self.e.last_checked:
            print('Never been checked before')
            run_refresher = True
        elif (datetime.datetime.now() - self.e.last_checked).total_seconds() >= update_interval:
            print('It has been {} hours since the last sync.'.format(self.refresh_interval))
            run_refresher = True

        if not run_refresher:
            return

        # Download URL
        success = False
        try:
            self.log('run', 'Downloading URL {}'.format(self.e.url.decode()))
            msg_bytes = self.e.fetch_msg_url()
        except URLDownloadError as e:
            err = 'Failed to download: Check your internet connection'
        except ProxyURLDownloadError as e:
            err = 'Failed to download: Check your internet connection and proxy configuration'
        else:
            success = True

        if not success:
            return self.finish_with_failure(err)

        if self.should_cancel:
            return self.finish_with_cancel()

        # Download signature URL
        success = False
        try:
            self.log('run', 'Downloading URL {}'.format(self.e.sig_url.decode()))
            msg_sig_bytes = self.e.fetch_msg_sig_url()
        except URLDownloadError as e:
            err = 'Failed to download: Check your internet connection'
        except ProxyURLDownloadError as e:
            err = 'Failed to download: Check your internet connection and proxy configuration'
        else:
            success = True

        if not success:
            return self.finish_with_failure(err)

        if self.should_cancel:
            return self.finish_with_cancel()

        # Fetch signing key from keyserver, make sure it's not expired or revoked
        success = False
        reset_last_checked = True
        try:
            self.log('run', 'Fetching public key {} {}'.format(self.c.fp_to_keyid(self.e.fingerprint).decode(), self.c.gpg.get_uid(self.e.fingerprint)))
            self.e.fetch_public_key(self.c.gpg)
        except InvalidFingerprint:
            err = 'Invalid signing key fingerprint'
        except NotFoundOnKeyserver:
            err = 'Signing key is not found on keyserver'
        except NotFoundInKeyring:
            err = 'Signing key is not found in keyring'
        except RevokedKey:
            err = 'The signing key is revoked'
        except ExpiredKey:
            err = 'The signing key is expired'
        except KeyserverError:
            err = 'Error connecting to keyserver'
            reset_last_checked = False
        else:
            success = True

        if not success:
            return self.finish_with_failure(err, reset_last_checked)

        if self.should_cancel:
            return self.finish_with_cancel()

        # Verifiy signature
        success = False
        try:
            self.log('run', 'Verifying signature')
            self.e.verify_fingerprints_sig(self.c.gpg, msg_sig_bytes, msg_bytes)
        except VerificationError:
            err = 'Signature does not verify'
        except BadSignature:
            err = 'Bad signature'
        except RevokedKey:
            err = 'The signing key is revoked'
        except SignedWithWrongKey:
            err = 'Valid signature, but signed with wrong signing key'
        else:
            success = True

        if not success:
            return self.finish_with_failure(err)

        if self.should_cancel:
            return self.finish_with_cancel()

        # Get fingerprint list
        success = False
        try:
            self.log('run', 'Validating fingerprints')
            fingerprints = self.e.get_fingerprint_list(msg_bytes)
        except InvalidFingerprints as e:
            err = 'Invalid fingerprints: {}'.format(e)
        else:
            success = True

        if not success:
            return self.finish_with_failure(err)

        if self.should_cancel:
            return self.finish_with_cancel()

        # Build list of fingerprints to fetch
        fingerprints_to_fetch = []
        invalid_fingerprints = []
        for fingerprint in fingerprints:
            try:
                self.c.gpg.test_key(fingerprint)
            except InvalidFingerprint:
                invalid_fingerprints.append(fingerprint)
            except (NotFoundInKeyring, ExpiredKey):
                # Fetch these ones
                fingerprints_to_fetch.append(fingerprint)
            except RevokedKey:
                # Skip revoked keys
                pass
            else:
                # Fetch all others
                fingerprints_to_fetch.append(fingerprint)

        # Communicate
        total_keys = len(fingerprints_to_fetch)
        current_key = 0
        self.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, current_key)

        # Fetch fingerprints
        notfound_fingerprints = []
        for fingerprint in fingerprints_to_fetch:
            try:
                self.log('run', 'Fetching public key {} {}'.format(self.c.fp_to_keyid(fingerprint).decode(), self.c.gpg.get_uid(fingerprint)))
                self.c.gpg.recv_key(self.e.keyserver, fingerprint, self.e.use_proxy, self.e.proxy_host, self.e.proxy_port)
            except KeyserverError:
                return self.finish_with_failure('Keyserver error')
            except NotFoundOnKeyserver:
                notfound_fingerprints.append(fingerprint)

            current_key += 1
            self.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, current_key)

            if self.should_cancel:
                return self.finish_with_cancel()

        # All done
        self.success.emit(self.e, invalid_fingerprints, notfound_fingerprints)
