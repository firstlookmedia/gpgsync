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
import json
from io import BytesIO

from .gnupg import *


class URLDownloadError(Exception):
    pass


class ProxyURLDownloadError(Exception):
    pass


class KeylistNotJson(Exception):
    pass


class KeylistInvalid(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


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

        # The decoded JSON object
        self.keylist_obj = None

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
        gpg.recv_key(self.get_keyserver(), self.fingerprint, self.use_proxy, self.proxy_host, self.proxy_port)

        # Test the key for issues
        gpg.test_key(self.fingerprint)

        # Save it to disk
        gpg.export_pubkey_to_disk(self.fingerprint)

    def fetch_msg_url(self):
        return self.fetch_url(self.url)

    def fetch_msg_sig_url(self):
        return self.fetch_url(self.get_msg_sig_url())

    def get_msg_sig_url(self):
        return self.keylist_obj['metadata']['signature_uri']

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

    def verify_sig(self, gpg, msg_sig_bytes, msg_bytes):
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

    def validate_format(self, msg_bytes):
        """
        Try to decode the message into a JSON object. Also, make sure it
        has all of the required fields.

        Note, this function stores the decoded object in self.keylist_obj,
        so it must be run before the keylist can be worked with.
        """
        # Try decoding JSON
        try:
            self.keylist_obj = json.loads(msg_bytes)
        except json.decoder.JSONDecodeError:
            raise KeylistNotJson()

        # Make sure the keylist JSON object has all required keys and values
        if 'metadata' not in self.keylist_obj:
            raise KeylistInvalid('Invalid keylist format: keylist["metadata"] key is missing')
        if 'signature_uri' not in self.keylist_obj['metadata']:
            raise KeylistInvalid('Invalid keylist format: keylist["metadata"]["signature_uri"] key is missing')
        if 'keys' not in self.keylist_obj:
            raise KeylistInvalid('Invalid keylist format: keylist["keys"] key is missing')
        if type(self.keylist_obj['keys']) is not list:
            raise KeylistInvalid('Invalid keylist format: keylist["keys"] is not an array')

        # Make sure each key has all the required keys and values
        for i in range(len(self.keylist_obj['keys'])):
            if type(self.keylist_obj['keys'][i]) is not dict:
                raise KeylistInvalid('Invalid keylist format: keylist["keys"][{}] is not an object'.format(i))
            if 'fingerprint' not in self.keylist_obj['keys'][i]:
                raise KeylistInvalid('Invalid keylist format: keylist["keys"][{}]["fingerprint"] key is missing'.format(i))
            if not self.c.valid_fp(self.keylist_obj['keys'][i]['fingerprint']):
                raise KeylistInvalid('Invalid keylist format: keylist["keys"][{}]["fingerprint"] is not a valid OpenPGP fingerprint'.format(i))

        # Make sure signature URI is in the right format
        o = urlparse(self.keylist_obj['metadata']['signature_uri'])
        if (o.scheme != 'http' and o.scheme != 'https') or o.netloc == '':
            raise KeylistInvalid('Signature URI is invalid.')

    def should_refresh(self, force):
        """
        Based on the info stored in the keylist, should we refresh it?
        """
        # Refresh if it's forced, if it's never been checked before,
        # or if it's been longer than the configured refresh interval
        update_interval = 60*60*float(self.c.settings.update_interval_hours)

        if force:
            self.c.log("Keylist", "should_refresh", "Forcing sync")
            return True

        if not self.last_checked:
            self.c.log("Keylist", "should_refresh", "Never been checked before")
            return True

        if (datetime.datetime.now() - self.last_checked).total_seconds() >= update_interval:
            self.c.log("Keylist", "should_refresh", "It has been {} hours since the last sync.".format(self.c.settings.update_interval_hours))
            return True

        return False

    def get_keyserver(self):
        """
        Figure out which keyserver will be used.
        """
        # If the user specified a keyserver, always use that first
        if self.keyserver != None:
            return self.keyserver

        # If the keylist specified a keyserver, use that
        if 'keyserver' in self.keylist_obj['metadata']:
            return self.keylist_obj['metadata']['keylist']

        # Fallback to Ubuntu's keyserver (since it seems better managed than the SKS pool)
        return 'hkps://keyserver.ubuntu.com/'

    def result_object(type, message=None, exception=None, data=None):
        """
        Returns an object that can be further evaluated.
        """
        return {
            "type": type,
            "message": message,
            "exception": exception,
            "data": data
        }

    def validate_authority_key(self):
        """
        Fetches the authority key from keyservers.
        Returns a result object.
        """
        # Fetch signing key from keyserver, make sure it's not expired or revoked
        try:
            self.c.log('Keylist', 'validate_authority_key', 'Fetching public key {} {}'.format(self.c.fp_to_keyid(self.fingerprint).decode(), self.c.gpg.get_uid(self.fingerprint)))
            self.fetch_public_key(self.c.gpg)
            return self.result_object('success')
        except InvalidFingerprint:
            return self.result_object('error', 'Invalid authority key fingerprint', data={"reset_last_checked": True})
        except NotFoundOnKeyserver:
            return self.result_object('error', 'Authority key is not found on keyserver', data={"reset_last_checked": True})
        except NotFoundInKeyring:
            return self.result_object('error', 'Authority key is not found in keyring', data={"reset_last_checked": True})
        except RevokedKey:
            return self.result_object('error', 'The authority key is revoked', data={"reset_last_checked": True})
        except ExpiredKey:
            return self.result_object('error', 'The authority key is expired', data={"reset_last_checked": True})
        except KeyserverError:
            return self.result_object('error', 'Error connecting to keyserver', data={"reset_last_checked": False})

    def refresh_keylist_uri(self):
        """
        Downloads the keylist URI.
        Returns a result object, with msg_bytes as data.
        """
        try:
            self.c.log('Keylist', 'refresh_keylist_uri', 'Downloading {}'.format(self.url.decode()))
            msg_bytes = self.fetch_msg_url()
            return self.result_object('success', data=msg_bytes)
        except URLDownloadError as e:
            return self.result_object('error', 'Failed to download: Check your internet connection')
        except ProxyURLDownloadError as e:
            return self.result_object('error', 'Failed to download: Check your internet connection and proxy configuration')

    def refresh_keylist_signature_uri(self):
        """
        Downloads the keylist signature URI.
        Returns a result object, with msg_sig_bytes as data.
        """
        try:
            msg_sig_url = self.get_msg_sig_url()
            self.c.log('Keylist', 'refresh_keylist_signature_uri', 'Downloading {}'.format(msg_sig_url))
            msg_sig_bytes = self.fetch_msg_sig_url()
            return self.result_object('success', data=msg_sig_bytes)
        except URLDownloadError as e:
            return self.result_object('error', 'Failed to download: Check your internet connection')
        except ProxyURLDownloadError as e:
            return self.result_object('error', 'Failed to download: Check your internet connection and proxy configuration')

    def refresh_verify_signature(self, msg_sig_bytes, msg_bytes):
        """
        Verify the signature.
        Returns a result object, with msg_sig_bytes as data.
        """
        try:
            self.c.log('Keylist', 'refresh', 'Verifying signature')
            self.verify_sig(self.c.gpg, msg_sig_bytes, msg_bytes)
        except VerificationError:
            return self.result_object('error', 'Signature does not verify')
        except BadSignature:
            return self.result_object('error', 'Bad signature')
        except RevokedKey:
            return self.result_object('error', 'The signing key is revoked')
        except SignedWithWrongKey:
            return self.result_object('error', 'Valid signature, but signed with wrong signing key')

    def refresh_build_fingerprints_lists(self, fingerprints):
        """
        Takes a list of fingerprints, returns a tuple that contains a list
        of fingerprints to fetch, and a list of invalid fingerprints
        """
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

        return (fingerprints_to_fetch, invalid_fingerprints)

    def refresh_fetch_fingerprints(self, fingerprints_to_fetch, total_keys, cancel_q):
        """
        Takes a list of fingerprints to fetch, and loops through it fetching
        them all. Returns a result object. On success, the result's data
        includes a list of fingerprints that weren't found.
        """
        current_key = 0
        notfound_fingerprints = []
        for fingerprint in fingerprints_to_fetch:
            try:
                self.c.log('Keylist', 'refresh_fetch_fingerprints', 'Fetching public key {} {}'.format(self.c.fp_to_keyid(fingerprint).decode(), self.c.gpg.get_uid(fingerprint)))
                self.c.gpg.recv_key(self.keyserver, fingerprint, self.use_proxy, self.proxy_host, self.proxy_port)
            except KeyserverError:
                return self.result_object('error', 'Keyserver error')
            except NotFoundOnKeyserver:
                notfound_fingerprints.append(fingerprint)

            current_key += 1
            self.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, current_key)

            if cancel_q.qsize() > 0:
                self.c.log("Keylist", "refresh_fetch_fingerprints", "canceling early {}".format(keylist.url.decode()))
                return self.result_object('cancel')

        return self.result_object('success', data=notfound_fingerprints)

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
        common.log("Keylist", "refresh", "Refreshing keylist {}".format(keylist.url.decode()))
        keylist.q.add_message(RefresherMessageQueue.STATUS_STARTING)

        if not keylist.should_refresh(force=force):
            common.log("Keylist", "refresh", "Keylist doesn't need refreshing {}".format(keylist.url.decode()))
            return keylist.result_object('skip')

        # If there is no connection - skip
        if not common.internet_available():
            common.log("Keylist", "refresh", "No internet, skipping {}".format(keylist.url.decode()))
            return keylist.result_object('skip')

        # Download keylist URI
        result = keylist.refresh_keylist_uri()
        if result['type'] == 'success':
            msg_bytes = result['data']
        else:
            return result

        if cancel_q.qsize() > 0:
            common.log("Keylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Make sure the keylist is in the correct format
        try:
            keylist.validate_format(msg_bytes)
        except KeylistNotJson as e:
            # If the keylist isn't in JSON format, is it a legacy keylist?
            common.log("Keylist", "refresh", "Not a JSON keylist, testing for legacy keylist")
            try:
                legacy_keylist = LegacyKeylist(keylist)
                legacy_keylist.get_fingerprint_list(msg_bytes)

                # No exception yet? Let's treat it as a legacy keylist then
                common.log("Keylist", "refresh", "Looks like a legacy keylist, so treat it like one")
                return LegacyKeylist.refresh(common, cancel_q, legacy_keylist, force)

            except InvalidFingerprints:
                # Not a legacy keylist, throw error
                common.log("Keylist", "refresh", "Not a JSON keylist or legacy keylist")
                return keylist.result_object('error', 'Keylist is not in JSON format.', e)
        except KeylistInvalid as e:
            return keylist.result_object('error', e.reason)

        # Download keylist signature URI
        result = keylist.refresh_keylist_signature_uri()
        if result['type'] == 'success':
            msg_sig_bytes = result['data']
        else:
            return result

        if cancel_q.qsize() > 0:
            common.log("Keylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Validate the authority key
        result = keylist.validate_authority_key()
        if result['type'] != 'success':
            return result

        if cancel_q.qsize() > 0:
            common.log("Keylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Verify signature
        result = keylist.refresh_verify_signature(msg_sig_bytes, msg_bytes)
        if result['type'] != 'success':
            return result

        if cancel_q.qsize() > 0:
            common.log("Keylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Communicate
        total_keys = len(keylist.keylist_obj['keys'])
        keylist.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, 0)

        # Build list of fingerprints to fetch
        fingerprints = [key['fingerprint'] for key in keylist.keylist_obj['keys']]
        fingerprints_to_fetch, invalid_fingerprints = keylist.refresh_build_fingerprints_lists(fingerprints)

        # Fetch fingerprints
        result = keylist.refresh_fetch_fingerprints(fingerprints_to_fetch, total_keys, cancel_q)
        if result['type'] == 'success':
            notfound_fingerprints = result['data']
        else:
            return result

        # All done
        return keylist.result_object('success', data={
            "keylist": keylist,
            "invalid_fingerprints": invalid_fingerprints,
            "notfound_fingerprints": notfound_fingerprints
        })


class LegacyKeylist(Keylist):
    """
    This is a legacy keylist, from before GPG Sync 0.3.0, and before the
    Keylist RFC changed the keylist format to be based on JSON.
    """
    def __init__(self, keylist):
        super(LegacyKeylist, self).__init__(keylist.c)
        self.c = keylist.c
        self.fingerprint = keylist.fingerprint
        self.url = keylist.url
        self.keyserver = keylist.keyserver
        self.use_proxy = keylist.use_proxy
        self.proxy_host = keylist.proxy_host
        self.proxy_port = keylist.proxy_port
        self.last_checked = keylist.last_checked
        self.last_synced = keylist.last_synced
        self.last_failed = keylist.last_failed
        self.error = keylist.error
        self.warning = keylist.warning
        self.q = keylist.q

    def get_keyserver(self):
        """
        Figure out which keyserver will be used. In legacy keylist, always
        just use the keyserver in the keylist object
        """
        return self.keyserver

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

    def get_msg_sig_url(self):
        return self.url + b'.sig'

    @staticmethod
    def refresh(common, cancel_q, keylist, force=False):
        """
        This function syncs a legacy keylist. It's exactly like Keylist.refresh,
        except it uses the legacy file format instead.
        """
        common.log("LegacyKeylist", "refresh", "Refreshing keylist {}".format(keylist.url.decode()))
        keylist.q.add_message(RefresherMessageQueue.STATUS_STARTING)

        if not keylist.should_refresh(force=force):
            common.log("LegacyKeylist", "refresh", "Keylist doesn't need refreshing {}".format(keylist.url.decode()))
            return keylist.result_object('skip')

        # If there is no connection - skip
        if not common.internet_available():
            common.log("LegacyKeylist", "refresh", "No internet, skipping {}".format(keylist.url.decode()))
            return keylist.result_object('skip')

        # Download keylist URI
        result = keylist.refresh_keylist_uri()
        if result['type'] == 'success':
            msg_bytes = result['data']
        else:
            return result

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Download keylist signature URI
        result = keylist.refresh_keylist_signature_uri()
        if result['type'] == 'success':
            msg_sig_bytes = result['data']
        else:
            return result

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Validate the authority key
        result = keylist.validate_authority_key()
        if result != True:
            return result

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Verify signature
        result = keylist.refresh_verify_signature()
        if result['type'] != 'success':
            return result

        if cancel_q.qsize() > 0:
            common.log("LegacyKeylist", "refresh", "canceling early {}".format(keylist.url.decode()))
            return keylist.result_object('cancel')

        # Build list of fingerprints to fetch
        try:
            fingerprints = keylist.get_fingerprint_list(msg_bytes)
        except InvalidFingerprints as e:
            return keylist.result_object('error', 'Invalid fingerprints: {}'.format(e))
        fingerprints_to_fetch, invalid_fingerprints = keylist.refresh_build_fingerprints_lists(fingerprints)

        # Communicate
        total_keys = len(fingerprints_to_fetch)
        keylist.q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, total_keys, 0)

        # Fetch fingerprints
        result = keylist.refresh_fetch_fingerprints(fingerprints_to_fetch, total_keys, cancel_q)
        if result['type'] == 'success':
            notfound_fingerprints = result['data']
        else:
            return result

        # All done
        return keylist.result_object('success', data={
            "keylist": keylist,
            "invalid_fingerprints": invalid_fingerprints,
            "notfound_fingerprints": notfound_fingerprints
        })
