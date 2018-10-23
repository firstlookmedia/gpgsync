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


class ValidatorMessageQueue(queue.LifoQueue):
    def __init(self):
        super(ValidatorMessageQueue, self).__init__()

    def add_message(self, msg, step):
        self.put({
            'msg': msg,
            'step': step
        })


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


class Keylist(object):
    """
    This represents a keylist. It complies with the Keylist RFC draft:
    https://datatracker.ietf.org/doc/draft-mccain-keylist/
    """
    def __init__(self, common):
        self.c = common

        self.fingerprint = b''
        self.url = b''
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

    def load(self, e):
        """
        Acts as a secondary constructor to load an keylist from settings
        """
        self.fingerprint = str.encode(e['fingerprint'])
        self.url = str.encode(e['url'])
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

        # Serialize only the attributes that should persist
        keys = ['fingerprint', 'url', 'keyserver', 'use_proxy',  'proxy_host',
                'proxy_port', 'last_checked', 'last_synced', 'last_failed',
                'error', 'warning']
        for k, v in self.__dict__.items():
            if k in keys:
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

    def fetch_msg_url(self):
        return self.fetch_url(self.url)

    def fetch_msg_sig_url(self):
        return self.fetch_url(self.url + b'.sig')

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

    def interpret_result(self, result):
        """
        After syncing, depending on how the refresh went, update timestamps
        and warning in the keylist and saving settings if necessary.
        """
        if result['type'] == "success":
            self.c.log("Keylist", "interpret_result", "refresh success")

            if len(result['data']['invalid_fingerprints']) == 0 and len(result['data']['notfound_fingerprints']) == 0:
                warning = False
            else:
                warnings = []
                if len(result['data']['invalid_fingerprints']) > 0:
                    warning.append('Invalid fingerprints: {}'.format(', '.join([x.decode() for x in result['data']['invalid_fingerprints']])))
                if len(result['data']['notfound_fingerprints']) > 0:
                    warnings.append('Fingerprints not found: {}'.format(', '.join([x.decode() for x in result['data']['notfound_fingerprints']])))
                warning = ', '.join(warnings)

            self.last_checked = datetime.datetime.now()
            self.last_synced = datetime.datetime.now()
            self.warning = warning
            self.error = None

            self.c.settings.save()

        elif result['type'] == "cancel":
            self.c.log("Keylist", "interpret_result", "refresh canceled")

        elif result['type'] == "error":
            self.c.log("Keylist", "interpret_result", "refresh error")

            if result['data']['reset_last_checked']:
                self.last_checked = datetime.datetime.now()
            self.last_failed = datetime.datetime.now()
            self.warning = None
            self.error = result['data']['message']

            self.c.settings.save()

    @staticmethod
    def result_object(type, message=None, exception=None, data=None):
        return {
            "type": type,
            "message": message,
            "exception": exception,
            "data": data
        }

    @staticmethod
    def validate_log(common, q, message, step=0):
        common.log("Keylist", "validate", message)
        q.add_message(message, step)


class LegacyKeylist(Keylist):
    """
    This is a legacy keylist, from before GPG Sync 0.3.0, and before the
    Keylist RFC changed the keylist format to be based on JSON.
    """
    def __init__(self, common):
        super(LegacyKeylist, self).__init__(common)
        self.c = common

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

    @staticmethod
    def validate(common, keylist):
        """
        This function validates that a keylist should work to sync.
        q should be a ValidatorMessageQueue object, and keylist is the
        keylist to validate.

        It returns a result object with type "error" on error and
        "success" on success.
        """
        common.log("LegacyKeylist", "validate", "Validating keylist {}".format(keylist.url.decode()))

        # Test loading URL
        try:
            LegacyKeylist.validate_log(common, keylist.q, 'Testing downloading URL {}'.format(keylist.url.decode()), 0)
            msg_bytes = keylist.fetch_msg_url()
        except ProxyURLDownloadError as e:
            return LegacyKeylist.result_object('error', 'URL failed to download: Check your internet connection and proxy settings.', e)
        except URLDownloadError as e:
            return LegacyKeylist.result_object('error', 'URL failed to download: Check your internet connection.', e)

        # Test loading signature URL
        try:
            LegacyKeylist.validate_log(common, keylist.q, 'Testing downloading URL {}'.format((keylist.url + b'.sig').decode()), 1)
            msg_sig_bytes = keylist.fetch_msg_sig_url()
        except ProxyURLDownloadError as e:
            return LegacyKeylist.result_object('error', 'URL failed to download: Check your internet connection and proxy settings.', e)
        except URLDownloadError as e:
            return LegacyKeylist.result_object('error', 'URL failed to download: Check your internet connection.', e)

        # Test fingerprint and keyserver, and that the key isn't revoked or expired
        try:
            LegacyKeylist.validate_log(common, keylist.q, 'Downloading {} from keyserver {}'.format(keylist.c.fp_to_keyid(keylist.fingerprint).decode(), keylist.keyserver.decode()), 2)
            keylist.fetch_public_key(common.gpg)
        except InvalidFingerprint:
            return LegacyKeylist.result_object('error', 'Invalid signing key fingerprint.')
        except KeyserverError:
            return LegacyKeylist.result_object('error', 'Error with keyserver {}.'.format(keylist.keyserver.decode()))
        except NotFoundOnKeyserver:
            return LegacyKeylist.result_object('error', 'Signing key is not found on keyserver. Upload signing key and try again.')
        except NotFoundInKeyring:
            return LegacyKeylist.result_object('error', 'Signing key is not found in keyring. Something went wrong.')
        except RevokedKey:
            return LegacyKeylist.result_object('error', 'The signing key is revoked.')
        except ExpiredKey:
            return LegacyKeylist.result_object('error', 'The signing key is expired.')

        # Make sure URL is in the right format
        o = urlparse(keylist.url)
        if (o.scheme != b'http' and o.scheme != b'https') or o.netloc == '':
            return LegacyKeylist.result_object('error', 'URL is invalid.')

        # After downloading URL, test that it's signed by signing key
        try:
            LegacyKeylist.validate_log(common, keylist.q, 'Verifying signature', 3)
            keylist.verify_fingerprints_sig(common.gpg, msg_sig_bytes, msg_bytes)
        except VerificationError:
            return LegacyKeylist.result_object('error', 'Signature does not verify.')
        except BadSignature:
            return LegacyKeylist.result_object('error', 'Bad signature.')
        except RevokedKey:
            return LegacyKeylist.result_object('error', 'The signing key is revoked.')
        except SignedWithWrongKey:
            return LegacyKeylist.result_object('error', 'Valid signature, but signed with wrong signing key.')

        # Test that it's a list of fingerprints
        try:
            LegacyKeylist.validate_log(common, keylist.q, 'Validating fingerprint list', 4)
            keylist.get_fingerprint_list(msg_bytes)
        except InvalidFingerprints as e:
            return LegacyKeylist.result_object('error', 'Invalid fingerprints', e)

        LegacyKeylist.validate_log(common, keylist.q, 'Keylist saved', 5)
        return LegacyKeylist.result_object('success')

    @staticmethod
    def refresh(common, cancel_q, keylist, force=False):
        """
        This function syncs a keylist, importing all of the public key.
        q should be a RefresherMessageQueue object, and keylist is the
        keylist to sync.
        cancel_q is a queue.Queue that can be used to cancel the refresh
        early. Push a True onto the queue to cancel.

        It returns a result object of type "error" on error, "skip" if
        there's no error but the keylist is getting skipped, "cancel"
        if the refresh gets canceled early, and "success" on success.
        """
        common.log("LegacyKeylist", "refresh", "Refreshing keylist {}".format(keylist.url.decode()))
        keylist.q.add_message(RefresherMessageQueue.STATUS_STARTING)

        # Refresh if it's forced, if it's never been checked before,
        # or if it's been longer than the configured refresh interval
        update_interval = 60*60*float(common.settings.update_interval_hours)
        run_refresher = False

        if force:
            common.log("LegacyKeylist", "refresh", "Forcing sync")
            run_refresher = True
        elif not keylist.last_checked:
            common.log("LegacyKeylist", "refresh", "Never been checked before")
            run_refresher = True
        elif (datetime.datetime.now() - keylist.last_checked).total_seconds() >= update_interval:
            common.log("LegacyKeylist", "refresh", "It has been {} hours since the last sync.".format(common.settings.update_interval_hours))
            run_refresher = True

        if not run_refresher:
            common.log("LegacyKeylist", "refresh", "Keylist doesn't need refreshing {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('skip')

        # If there is no connection - skip
        if not common.internet_available():
            common.log("LegacyKeylist", "refresh", "No internet, skipping {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('skip')

        # Download URL
        try:
            common.log('run', 'Downloading URL {}'.format(keylist.url.decode()))
            msg_bytes = keylist.fetch_msg_url()
        except URLDownloadError as e:
            return LegacyKeylist.result_object('error', 'Failed to download: Check your internet connection')
        except ProxyURLDownloadError as e:
            return LegacyKeylist.result_object('error', 'Failed to download: Check your internet connection and proxy configuration')

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('cancel')

        # Download signature URL
        try:
            common.log('run', 'Downloading URL {}'.format((keylist.url + b'.sig').decode()))
            msg_sig_bytes = keylist.fetch_msg_sig_url()
        except URLDownloadError as e:
            return LegacyKeylist.result_object('error', 'Failed to download: Check your internet connection')
        except ProxyURLDownloadError as e:
            return LegacyKeylist.result_object('error', 'Failed to download: Check your internet connection and proxy configuration')

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('cancel')

        # Fetch signing key from keyserver, make sure it's not expired or revoked
        try:
            common.log('run', 'Fetching public key {} {}'.format(common.fp_to_keyid(keylist.fingerprint).decode(), common.gpg.get_uid(keylist.fingerprint)))
            keylist.fetch_public_key(common.gpg)
        except InvalidFingerprint:
            return LegacyKeylist.result_object('error', 'Invalid signing key fingerprint', data={"reset_last_checked": True})
        except NotFoundOnKeyserver:
            return LegacyKeylist.result_object('error', 'Signing key is not found on keyserver', data={"reset_last_checked": True})
        except NotFoundInKeyring:
            return LegacyKeylist.result_object('error', 'Signing key is not found in keyring', data={"reset_last_checked": True})
        except RevokedKey:
            return LegacyKeylist.result_object('error', 'The signing key is revoked', data={"reset_last_checked": True})
        except ExpiredKey:
            return LegacyKeylist.result_object('error', 'The signing key is expired', data={"reset_last_checked": True})
        except KeyserverError:
            return LegacyKeylist.result_object('error', 'Error connecting to keyserver', data={"reset_last_checked": False})

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('cancel')

        # Verifiy signature
        try:
            common.log('run', 'Verifying signature')
            keylist.verify_fingerprints_sig(common.gpg, msg_sig_bytes, msg_bytes)
        except VerificationError:
            return LegacyKeylist.result_object('error', 'Signature does not verify')
        except BadSignature:
            return LegacyKeylist.result_object('error', 'Bad signature')
        except RevokedKey:
            return LegacyKeylist.result_object('error', 'The signing key is revoked')
        except SignedWithWrongKey:
            return LegacyKeylist.result_object('error', 'Valid signature, but signed with wrong signing key')

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('cancel')

        # Get fingerprint list
        try:
            common.log('run', 'Validating fingerprints')
            fingerprints = keylist.get_fingerprint_list(msg_bytes)
        except InvalidFingerprints as e:
            return LegacyKeylist.result_object('error', 'Invalid fingerprints: {}'.format(e))

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return LegacyKeylist.result_object('cancel')

        # Build list of fingerprints to fetch
        fingerprints_to_fetch = []
        invalid_fingerprints = []
        for fingerprint in fingerprints:
            try:
                common.gpg.test_key(fingerprint)
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
        keylist.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, current_key)

        # Fetch fingerprints
        notfound_fingerprints = []
        for fingerprint in fingerprints_to_fetch:
            try:
                common.log('run', 'Fetching public key {} {}'.format(common.fp_to_keyid(fingerprint).decode(), common.gpg.get_uid(fingerprint)))
                common.gpg.recv_key(keylist.keyserver, fingerprint, keylist.use_proxy, keylist.proxy_host, keylist.proxy_port)
            except KeyserverError:
                return LegacyKeylist.result_object('error', 'Keyserver error')
            except NotFoundOnKeyserver:
                notfound_fingerprints.append(fingerprint)

            current_key += 1
            keylist.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, current_key)

            if cancel_q.qsize() > 0:
                common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
                return LegacyKeylist.result_object('cancel')

        # All done
        return LegacyKeylist.result_object('success', data={
            "keylist": keylist,
            "invalid_fingerprints": invalid_fingerprints,
            "notfound_fingerprints": notfound_fingerprints
        })
