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
import re
import subprocess
import os
import tempfile
import shutil
from urllib.parse import urlparse


class InvalidFingerprint(Exception):
    pass


class KeyserverError(Exception):
    pass


class NotFoundOnKeyserver(Exception):
    pass


class NotFoundInKeyring(Exception):
    pass


class RevokedKey(Exception):
    pass


class ExpiredKey(Exception):
    pass


class VerificationError(Exception):
    pass


class BadSignature(Exception):
    pass


class SignedWithWrongKey(Exception):
    pass


class GnuPG(object):
    def __init__(self, common, appdata_path=None):
        self.appdata_path = appdata_path
        self.c = common

        self.homedir = tempfile.mkdtemp()
        self.c.log("GnuPG", "__init__", "created homedir: {}".format(self.homedir))

        self.system = self.c.os
        self.popen_startupinfo = None
        self.creationflags = 0
        if self.system == 'Darwin':
            os.environ['PATH'] = '/bin:/usr/bin:/usr/local/bin'
            self.gpg_path = shutil.which('gpg')
        elif self.system == 'Linux':
            self.gpg_path = shutil.which('gpg2')
        elif self.system == 'Windows':
            import win32process
            self.creationflags = win32process.CREATE_NO_WINDOW
            self.gpg_path = "C:/Program Files (x86)/GnuPG/bin/gpg.exe"

            # In Windows, hide console window when opening gpg.exe subprocess
            self.popen_startupinfo = subprocess.STARTUPINFO()
            self.popen_startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        # Remember uids that have already been queried
        self.uids = dict()

    def __del__(self):
        # Delete the temporary homedir
        shutil.rmtree(self.homedir, ignore_errors=True)
        self.c.log("GnuPG", "__del__", "deleted homedir: {}".format(self.homedir))

    def is_gpg_available(self):
        if self.system == 'Windows':
            try:
                return os.path.isfile(self.gpg_path)
            except:
                return False
        else:
            try:
                return os.path.isfile(self.gpg_path) and os.access(self.gpg_path, os.X_OK)
            except:
                return False

    def recv_key(self, keyserver, fp, use_proxy, proxy_host, proxy_port):
        self.c.log("GnuPG", "recv_key", "keyserver={}, fp={}, use_proxy={}, proxy_host={}, proxy_port={}".format(keyserver, fp, use_proxy, proxy_host, proxy_port))

        if not self.c.valid_fp(fp):
            raise InvalidFingerprint(fp)

        fp = self.c.clean_fp(fp).decode()
        keyserver = self.c.clean_keyserver(keyserver).decode()

        default_hkps_server = 'hkps://hkps.pool.sks-keyservers.net'
        ca_cert_file = self.c.get_resource_path('sks-keyservers.netCA.pem')

        # Create gpg.conf and dirmngr.conf
        dirmngr_conf = ''
        gpg_conf = 'require-cross-certification\n'
        gpg_conf += 'keyserver {}\n'.format(keyserver)
        if keyserver == default_hkps_server:
            # Don't need to add ca_cert_file in OS X, because GPG Tools includes the
            # correct .pem for hkps://hkps.pool.sks-keyservers.net, and specifying it
            # breaks because of a space in the filename (in "GPG Sync.app")
            if not self.system == 'Darwin':
                gpg_conf += 'keyserver-options ca-cert-file={}\n'.format(ca_cert_file)
                dirmngr_conf += 'hkp-cacert {}\n'.format(ca_cert_file)
        open(os.path.join(self.homedir, 'dirmngr.conf'), 'w').write(dirmngr_conf)
        open(os.path.join(self.homedir, 'gpg.conf'), 'w').write(gpg_conf)

        args = ['--recv-keys', fp]
        out,err = self._gpg(args)

        if b"No keyserver available" in err or b"gpg: keyserver communications error: General error" in err or b"gpgkeys: HTTP fetch error" in out:
            raise KeyserverError(keyserver)

        if b"not found on keyserver" in err or b"keyserver receive failed: No data" in err or b"no valid OpenPGP data found" in err:
            raise NotFoundOnKeyserver(fp)

        if b"keyserver receive failed" in err:
            raise KeyserverError(keyserver)

        # Import key into default homedir
        self.import_to_default_homedir(fp)

    def get_pubkey_filename_on_disk(self, fp):
        fp = self.c.clean_fp(fp).decode()
        filename = fp + '.asc'
        return os.path.join(self.appdata_path, filename)

    def export_pubkey_to_disk(self, fp):
        fp = self.c.clean_fp(fp)
        filename = self.get_pubkey_filename_on_disk(fp)
        fp = fp.decode()

        self.c.log("GnuPG", "export_pubkey_to_disk", "fp={}".format(fp))

        if not self.appdata_path:
            self.c.log("GnuPG", "export_pubkey_to_disk", "appdata_path not set, skipping")
            return

        # Export public key from the temporary homedir
        out,err = self._gpg(['--armor', '--export', fp])
        pubkey = out

        # Save to disk
        open(filename, 'w').write(pubkey.decode())

    def import_pubkey_from_disk(self, fp):
        fp = self.c.clean_fp(fp)
        filename = self.get_pubkey_filename_on_disk(fp)
        fp = fp.decode()

        self.c.log("GnuPG", "import_pubkey_from_disk", "fp={}".format(fp))

        if not self.appdata_path:
            self.c.log("GnuPG", "import_pubkey_from_disk", "appdata_path not set, skipping")
            return

        # Import key
        try:
            out,err = self._gpg(['--import', filename])
        except:
            # If the key doesn't exist, ignore
            pass

    def delete_pubkey_from_disk(self, fp):
        fp = self.c.clean_fp(fp)
        filename = self.get_pubkey_filename_on_disk(fp)
        fp = fp.decode()

        self.c.log("GnuPG", "delete_pubkey_from_disk", "fp={}".format(fp))

        if not self.appdata_path:
            self.c.log("GnuPG", "delete_pubkey_from_disk", "appdata_path not set, skipping")
            return

        # Skip if the fingerprint is blank
        if fp == b"":
            return

        # Delete the public key from disk
        try:
            os.remove(filename)
        except:
            pass

    def test_key(self, fp):
        self.c.log("GnuPG", "test_key", "fp={}".format(fp))

        if not self.c.valid_fp(fp):
            raise InvalidFingerprint(fp)

        fp = self.c.clean_fp(fp).decode()
        out,err = self._gpg(['--with-colons', '--list-keys', fp])

        if b"error reading key: No public key" in err:
            raise NotFoundInKeyring(fp)

        for line in out.split(b'\n'):
            if line.startswith(b'pub:'):
                chunks = line.split(b':')
                if chunks[1] == b'r':
                    raise RevokedKey(fp)
                if chunks[1] == b'e':
                    raise ExpiredKey(fp)

    def get_uid(self, fp):
        self.c.log("GnuPG", "get_uid", "fp={}".format(fp))

        if not self.c.valid_fp(fp):
            raise InvalidFingerprint(fp)

        fp = self.c.clean_fp(fp).decode()

        if fp in self.uids:
            return self.uids[fp]

        out,err = self._gpg(['--with-colons', '--list-keys', fp])
        for line in out.split(b'\n'):
            if line.startswith(b'uid:'):
                chunks = line.split(b':')
                uid = str(chunks[9], 'UTF-8')
                self.uids[fp] = uid
                return uid

        return ''

    def verify(self, msg_sig, msg, fp):
        self.c.log("GnuPG", "verify," "(not displaying msg_sig, msg), fp={}".format(fp))

        if not self.c.valid_fp(fp):
            raise InvalidFingerprint(fp)

        fp = self.c.clean_fp(fp).decode()

        # Write message and detached signature to disk
        msg_sig_filename = tempfile.NamedTemporaryFile(delete=False).name
        open(msg_sig_filename, 'wb').write(msg_sig)
        msg_filename = tempfile.NamedTemporaryFile(delete=False).name
        open(msg_filename, 'wb').write(msg)

        # Verify the signature
        out,err = self._gpg(['--keyid-format', '0xlong', '--verify', msg_sig_filename, msg_filename])
        os.unlink(msg_filename)
        os.unlink(msg_sig_filename)

        if b'BAD signature' in err:
            raise BadSignature()
        if b"Can't check signature: No public key" in err or b'no valid OpenPGP data found' in err or b'the signature could not be verified' in err:
            raise VerificationError()
        if b'This key has been revoked by its owner!' in err:
            raise RevokedKey()
        if b'Note: This key has expired!' in err:
            raise ExpiredKey()
        if b'Signature made' not in err and b'Good signature from' not in err:
            raise VerificationError()

        # Make sure the signing key is correct
        lines = err.split(b'\n')
        for i in range(len(lines)):
            if lines[i].startswith(b'gpg: Signature made'):
                signing_fp = lines[i+1].split()[-1]
                signing_keyid = self.fp_to_long_keyid(signing_fp)
                if signing_keyid not in self.list_all_keyids(fp):
                    raise SignedWithWrongKey
                break

    def list_all_keyids(self, fp):
        self.c.log("GnuPG", "list_all_keyids", "fp={}".format(fp))

        if not self.c.valid_fp(fp):
            raise InvalidFingerprint(fp)

        fp = self.c.clean_fp(fp).decode()

        out, err = self._gpg(['--keyid-format', '0xlong', '--list-keys', fp])
        if b'gpg: error reading key: No public key' in err:
            raise NotFoundInKeyring

        return re.findall(b'0x[A-F\d]{16}', out)

    def fp_to_long_keyid(self, fp):
        if re.match(b'0x[A-F\d]{16}', fp):
            return fp
        return b'0x' + fp[-16:]

    def import_to_default_homedir(self, fp):
        self.c.log("GnuPG", "import_to_default_homedir", "fp={}".format(fp))

        # Export public key from the temporary homedir
        out,err = self._gpg(['--armor', '--export', fp])
        pubkey = out

        # Import public key into default homedir
        if not b'gpg: WARNING: nothing exported' in err:
            p = subprocess.Popen([self.gpg_path, '--import'],
                stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                startupinfo=self.popen_startupinfo)
            (out, err) = p.communicate(pubkey)

            if out != '':
                self.c.log("GnuPG", "import_to_default_homedir", "stdout: {}".format(out))
            if err != '':
                self.c.log("GnuPG", "import_to_default_homedir", "stderr: {}".format(err))

    def _gpg(self, args, input=None):
        default_args = [self.gpg_path, '--batch', '--no-tty', '--homedir', self.homedir]

        self.c.log("GnuPG", "_gpg", "args: {}".format(default_args + args))

        p = subprocess.Popen(default_args + args,
            stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
            startupinfo=self.popen_startupinfo)
        (out, err) = p.communicate(input)

        if out != '':
            # Only display the first 512 bytes
            if len(out) >= 512:
                display_out = out[0:512] + b'...';
            else:
                display_out = out
            self.c.log("GnuPG", "_gpg", "stdout: {}".format(display_out))
        if err != '':
            self.c.log("GnuPG", "_gpg", "stderr: {}".format(err))
        return out, err
