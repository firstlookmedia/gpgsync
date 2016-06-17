# -*- coding: utf-8 -*-
import requests, uuid, datetime
from io import BytesIO
from PyQt5 import QtCore, QtWidgets

from . import common
from .gnupg import *

class URLDownloadError(Exception):
    pass

class InvalidFingerprints(Exception):
    def __init__(self, fingerprints):
        self.fingerprints = fingerprints

    def __str__(self):
        return str([s.decode() for s in self.fingerprints])

class FingerprintsListNotSigned(Exception):
    pass

class Endpoint(object):
    def __init__(self):
        self.verified = False
        self.fingerprint = b''
        self.url = b'https://'
        self.keyserver = b'hkps://hkps.pool.sks-keyservers.net'
        self.use_proxy = False
        self.proxy_host = b'127.0.0.1'
        self.proxy_port = b'9050'
        self.last_checked = None
        self.error = None
        self.warning = None

    def fetch_public_key(self, gpg):
        # Retreive the signing key from the keyserver
        gpg.recv_key(self.keyserver, self.fingerprint, self.use_proxy, self.proxy_host, self.proxy_port)

        # Test the key for issues
        gpg.test_key(self.fingerprint)

    def fetch_url(self):
        try:
          if self.use_proxy:
            socks5_address = 'socks5://{0}:{1}'.format(self.proxy_host.decode("utf-8"), self.proxy_port.decode("utf-8"))

            proxies = {
              'https': socks5_address,
              'http': socks5_address
            }

            r = requests.get(self.url, proxies = proxies)
          else:
            r = requests.get(self.url)

          r.close()
          msg_bytes = r.content
        except requests.exceptions.RequestException as e:
          raise URLDownloadError(e)

        return  msg_bytes

    def verify_fingerprints_sig(self, gpg, msg_bytes):
        # Make sure the signature is valid
        gpg.verify(msg_bytes, self.fingerprint)

    def get_fingerprint_list(self, msg_bytes):
        # OpenPGP message format: https://tools.ietf.org/html/rfc4880

        if msg_bytes[-2:] == b'\r\n':
            sep = b'\r\n'
        else:
            sep = b'\n'

        cleartext_header = b'-----BEGIN PGP SIGNED MESSAGE-----' + sep
        sig_header = b'-----BEGIN PGP SIGNATURE-----' + sep
        sig_footer = b'-----END PGP SIGNATURE-----' + sep

        if cleartext_header not in msg_bytes or sig_header not in msg_bytes or sig_footer not in msg_bytes:
            raise FingerprintsListNotSigned

        # Get the content, plus armor headers and blank line
        start = msg_bytes.find(cleartext_header) + len(cleartext_header)
        end = msg_bytes.find(sig_header)
        content = msg_bytes[start:end]

        # Split the content into lines, and cut off the armor headers
        lines = content.split(sep)
        blank_i = None
        for i in range(len(lines)):
            if lines[i] == b'':
                blank_i = i
                break
        lines = lines[blank_i+1:]

        # Convert the content into a list of fingerprints
        fingerprints = []
        invalid_fingerprints = []
        for line in lines:
            # If there are comments in the line, remove the comments
            if b'#' in line:
                line = line.split(b'#')[0]

            # Skip blank lines
            if line.strip() == b'':
                continue

            # Test for valid fingerprints
            if common.valid_fp(line):
                fingerprints.append(line)
            else:
                invalid_fingerprints.append(line)

        if len(invalid_fingerprints) > 0:
            raise InvalidFingerprints(invalid_fingerprints)

        return fingerprints

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
        e.fingerprint = self.fingerprint
        e.url = self.url
        e.keyserver = self.keyserver
        e.use_proxy = self.use_proxy
        e.proxy_host = self.proxy_host
        e.proxy_port = self.proxy_port

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

        # Test fingerprint and keyserver, and that the key isn't revoked or expired
        success = False
        try:
            self.q.add_message('Downloading {} from keyserver {}'.format(common.fp_to_keyid(self.fingerprint).decode(), self.keyserver.decode()))
            e.fetch_public_key(self.gpg)
        except InvalidFingerprint:
            self.alert_error.emit('Invalid signing key fingerprint.')
        except InvalidKeyserver:
            self.alert_error.emit('Invalid keyserver.')
        except KeyserverError:
            self.alert_error.emit('Error with keyserver {}.'.format(self.keyserver.decode()))
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
            self.alert_error.emit('Invalid fingerprints: {}'.format(e))
        except FingerprintsListNotSigned:
            self.alert_error.emit('Fingerprints list is not signed.')
        else:
            success = True

        if not success:
            return self.finish_with_failure()

        self.q.add_message('Endpoint saved', timeout=4000)
        self.success.emit(self.fingerprint, self.url, self.keyserver, self.use_proxy, self.proxy_host, self.proxy_port)
        self.finished.emit()

class Refresher(QtCore.QThread):
    success = QtCore.pyqtSignal(Endpoint, list, list)
    error = QtCore.pyqtSignal(Endpoint, str, bool)

    def __init__(self, gpg, q, endpoint, force=False):
        super(Refresher, self).__init__()
        self.gpg = gpg
        self.q = q
        self.e = endpoint
        self.force = force

    def finish_with_failure(self, err, reset_last_checked=True):
        self.q.add_message(type='clear')
        self.error.emit(self.e, err, reset_last_checked)

    def run(self):
        # Refresh if it's forced, if it's never been checked before,
        # or if it's been 24 hours since last check
        one_day = 60*60*24
        if self.force or not self.e.last_checked or (datetime.datetime.now() - self.e.last_checked).seconds >= one_day:
            # Fetch signing key from keyserver, make sure it's not expired or revoked
            success = False
            reset_last_checked = True
            try:
                self.q.add_message('Fetching public key {} {}'.format(common.fp_to_keyid(self.e.fingerprint).decode(), self.gpg.get_uid(self.e.fingerprint)))
                self.e.fetch_public_key(self.gpg)
            except InvalidFingerprint:
                err = 'Invalid signing key fingerprint'
            except InvalidKeyserver:
                err = 'Invalid keyserver'
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

            # Download URL
            success = False
            try:
                self.q.add_message('Downloading URL {}'.format(self.e.url.decode()))
                msg_bytes = self.e.fetch_url()
            except URLDownloadError as e:
                err = 'URL failed to download: {}'.format(e)
            else:
                success = True

            if not success:
                return self.finish_with_failure(err)

            # Verifiy signature
            success = False
            try:
                self.q.add_message('Verifying signature')
                self.e.verify_fingerprints_sig(self.gpg, msg_bytes)
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

            # Get fingerprint list
            success = False
            try:
                self.q.add_message('Validating fingerprints')
                fingerprints = self.e.get_fingerprint_list(msg_bytes)
            except InvalidFingerprints as e:
                err = 'Invalid fingerprints: {}'.format(e)
            except FingerprintsListNotSigned:
                err = 'Fingerprints list is not signed'
            else:
                success = True

            if not success:
                return self.finish_with_failure(err)

            # Build list of fingerprints to fetch
            fingerprints_to_fetch = []
            invalid_fingerprints = []
            for fingerprint in fingerprints:
                try:
                    self.gpg.test_key(fingerprint)
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

            # Fetch fingerprints
            notfound_fingerprints = []
            for fingerprint in fingerprints_to_fetch:
                try:
                    self.q.add_message('Fetching public key {} {}'.format(common.fp_to_keyid(fingerprint).decode(), self.gpg.get_uid(fingerprint)))
                    self.gpg.recv_key(self.e.keyserver, fingerprint, self.e.use_proxy, self.e.proxy_host, self.e.proxy_port)
                except InvalidKeyserver:
                    return self.finish_with_failure('Invalid keyserver')
                except NotFoundOnKeyserver:
                    notfound_fingerprints.append(fingerprint)

            # All done
            self.success.emit(self.e, invalid_fingerprints, notfound_fingerprints)
