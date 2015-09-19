# -*- coding: utf-8 -*-
import pycurl, uuid
from io import BytesIO

from . import common

class URLDownloadError(Exception):
    pass

class InvalidFingerprints(Exception):
    pass

class FingerprintsListNotSigned(Exception):
    pass

class Endpoint(object):
    def __init__(self):
        # each endpoint needs a unique id
        self.id = uuid.uuid4()

        # set defaults
        self.update(fingerprint=b'', url=b'https://', keyserver=b'hkp://keys.gnupg.net',
            use_proxy=False, proxy_host=b'127.0.0.1', proxy_port=b'9050')

    def update(self, fingerprint=None, url=None, keyserver=None, use_proxy=None, proxy_host=None, proxy_port=None, last_checked=None):
        if fingerprint != None:
            self.fingerprint = fingerprint
        if url != None:
            self.url = url
        if keyserver != None:
            self.keyserver = keyserver
        if use_proxy != None:
            self.use_proxy = bool(use_proxy)
        if proxy_host != None:
            self.proxy_host = proxy_host
        if proxy_port != None:
            self.proxy_port = proxy_port
        if last_checked != None:
            self.last_checked = False

    def fetch_public_key(self, gpg):
        # Retreive the signing key from the keyserver
        gpg.recv_key(self.keyserver, self.fingerprint)

        # Test the key for issues
        gpg.test_key(self.fingerprint)

    def fetch_url(self):
        try:
            buffer = BytesIO()
            c = pycurl.Curl()
            c.setopt(pycurl.URL, self.url)
            c.setopt(c.WRITEDATA, buffer)
            if self.use_proxy:
                c.setopt(pycurl.PROXY, self.proxy_host)
                c.setopt(pycurl.PROXYPORT, int(self.proxy_port))
                c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5)
            c.perform()
            c.close()
            msg_bytes = buffer.getvalue()
        except pycurl.error as e:
            raise URLDownloadError(e)

        return msg_bytes

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
