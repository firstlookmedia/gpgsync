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
import datetime
import os
import sys
import re
import platform
import inspect
import requests
import socket
from urllib.parse import urlparse
from packaging.version import parse

from .gnupg import GnuPG, NotFoundOnKeyserver, KeyserverError
from .settings import Settings


class Common(object):
    """
    The Common class is a singleton of shared functionality throughout the app
    """
    def __init__(self, verbose):
        self.verbose = verbose

        # Define the OS
        self.os = platform.system()

        # Version of GPG Sync
        version_file = self.get_resource_path('version')
        self.version = parse(open(version_file).read().strip())

        # Load settings
        self.settings = Settings(self)

        # Initialize GnuPG
        self.gpg = GnuPG(self, appdata_path=self.settings.get_appdata_path())

    def log(self, module, func, msg=''):
        if self.verbose:
            final_msg = "[{}] {}".format(module, func)
            if msg:
                final_msg = "{}: {}".format(final_msg, msg)
            print(final_msg)

    def clean_fp(self, fp):
        if type(fp) == bytes:
            return fp.strip().replace(b' ', b'').upper()
        else:
            return fp.strip().replace(' ', '').upper().encode()

    def valid_fp(self, fp):
        return re.match(b'^[A-F\d]{40}$', self.clean_fp(fp))

    def fp_to_keyid(self, fp):
        return '0x{}'.format(self.clean_fp(fp)[-16:].decode()).encode()

    def clean_keyserver(self, keyserver):
        """
        Convert keyserver to format: protocol://domain:port
        """
        o = urlparse(keyserver)

        # Scheme and port
        scheme = o.scheme
        if scheme == b'hkp':
            port = 80
        elif scheme == b'hkps':
            port = 443
        else:
            scheme = b'hkp'
            port = 80

        # Domain
        domain = o.netloc
        if domain == b'':
            domain = o.path.strip(b'/')

        # Does the domain include a port?
        if b':' in domain:
            parts = domain.split(b':')
            domain = parts[0]
            port = int(parts[1])

        return scheme + b'://' + domain + b':' + str(port).encode()

    def get_resource_path(self, filename):
        if getattr(sys, 'gpgsync_dev', False):
            # Look for resources directory relative to python file
            prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), 'share')

        # Check if app is "frozen"
        # https://pythonhosted.org/PyInstaller/#run-time-information
        elif getattr(sys, 'frozen', False):
            prefix = os.path.join(os.path.dirname(sys.executable), 'share')

        elif self.os == 'Linux':
            prefix = os.path.join(sys.prefix, 'share/gpgsync')

        resource_path = os.path.join(prefix, filename)
        return resource_path

    def requests_get(self, url, proxies=None):
        # When creating an OSX app bundle, the requests module can't seem to find
        # the location of cacerts.pem. Here's a hack to let it know where it is.
        # https://stackoverflow.com/questions/17158529/fixing-ssl-certificate-error-in-exe-compiled-with-py2exe-or-pyinstaller
        if getattr(sys, 'frozen', False):
            if self.os == 'Darwin':
                verify = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Resources/certifi/cacert.pem')
            elif self.os == 'Windows':
                verify = os.path.join(os.path.dirname(sys.executable), 'certifi/cacert.pem')
            else:
                verify = None
            return requests.get(url, proxies=proxies, verify=verify)
        else:
            return requests.get(url, proxies=proxies)

    def serialize_settings(self, o):
        if isinstance(o, bytes):
            return o.decode()
        if isinstance(o, datetime.datetime):
            return o.isoformat()

    def internet_available(self):
        try:
            host = socket.gethostbyname("www.example.com")
            s = socket.create_connection((host, 80), 2)
            return True
        except:
            pass

        return False

    def vks_get_by_fingerprint(self, fp, use_proxy, proxy_host, proxy_port):
        """
        Download a public key from keys.openssl.org using the VKS interface:
        https://keys.openpgp.org/about/api
        """
        if use_proxy:
            api_endpoint = 'http://zkaan2xfbuxia2wpf7ofnkbz6r5zdbbvxbunvp5g2iebopbfc4iqmbad.onion/vks/v1'

            socks5_address = 'socks5h://{}:{}'.format(proxy_host.decode(), proxy_port.decode())
            proxies = {
                'https': socks5_address,
                'http': socks5_address
            }
        else:
            api_endpoint = 'https://keys.openpgp.org/vks/v1'
            proxies = None

        # Fetch the key by fingerprint
        r = self.requests_get("{}/by-fingerprint/{}".format(api_endpoint, fp), proxies)
        self.log("Common", "vks_get_by_fingerprint", "{} GET /by-fingerprint/{}".format(r.status_code, fp))

        if r.status_code == 404:
            raise NotFoundOnKeyserver(fp)
        if r.status_code != 200:
            raise KeyserverError("keys.openpgp.org: {}".format(r.text))

        # Return the ASCII-armored public key, in bytes
        return r.content
