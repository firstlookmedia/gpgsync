# -*- coding: utf-8 -*-
from nose import with_setup
from nose.tools import raises
from pgpsync import *
from pgpsync.gnupg import *

from .test_helpers import *

def test_gpg_is_available():
    gpg = GnuPG()
    assert gpg.is_gpg_available()

def test_gpg_recv_key():
    gpg = GnuPG()
    gpg.recv_key(b'hkp://keys.gnupg.net', test_key_fp, False, None, None)
    assert gpg.get_uid(test_key_fp) == 'PGP Sync Test Suite Key'

@raises(KeyserverError)
def test_gpg_recv_key_keyserver_error():
    gpg = GnuPG()
    gpg.recv_key(b'hkp://fakekeyserver', test_key_fp, False, None, None)

@raises(NotFoundOnKeyserver)
def test_gpg_recv_key_not_found_on_keyserver():
    gpg = GnuPG()
    gpg.recv_key(b'hkp://keys.gnupg.net', b'0000000000000000000000000000000000000000', False, None, None)

@raises(InvalidFingerprint)
def test_gpg_test_key_invalid_fingerprint():
    gpg = GnuPG()
    gpg.test_key(b'deadbeef')

@raises(NotFoundInKeyring)
def test_gpg_test_key_not_found_in_keyring():
    gpg = GnuPG()
    gpg.test_key(b'0000000000000000000000000000000000000000')

@raises(RevokedKey)
def test_gpg_test_key_revoked():
    gpg = GnuPG()
    import_key('revoked_pubkey.asc', gpg.homedir)
    gpg.test_key(b'A2A6 C99C A078 0A71 4F3C  2A17 3E67 1C4F 8C1A 99ED')

@raises(ExpiredKey)
def test_gpg_test_key_expired():
    gpg = GnuPG()
    import_key('expired_pubkey.asc', gpg.homedir)
    gpg.test_key(b'5256 2F09 247B 3EB0 B977  D46D 19A8 50C0 02BE 9F35')

def test_gpg_get_uid():
    gpg = GnuPG()
    import_key('pgpsync_multiple_uids.asc', gpg.homedir)
    import_key('pgpsync_test_suite_pubkey.asc', gpg.homedir)

    # should return the primary uid
    assert gpg.get_uid(b'D86B 4D4B B5DF DD37 8B58  D4D3 F121 AC62 3039 6C33') == 'PGP Sync Test uid 3 <pgpsync-uid3@example.com>'
    assert gpg.get_uid(b'ABCF D99F A161 7E55 B8CD  E5AD E36F D670 7779 47EB') == 'PGP Sync Test Suite Key'

def test_gpg_verify():
    # test a message that works to verify
    gpg = GnuPG()
    import_key('pgpsync_test_suite_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-valid.asc'), 'rb').read()
    gpg.verify(msg, b'ABCF D99F A161 7E55 B8CD  E5AD E36F D670 7779 47EB')

@raises(BadSignature)
def test_gpg_verify_invalid_sig():
    # test a message with an invalid sig
    gpg = GnuPG()
    import_key('pgpsync_test_suite_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-invalid.asc'), 'rb').read()
    gpg.verify(msg, b'ABCF D99F A161 7E55 B8CD  E5AD E36F D670 7779 47EB')

@raises(RevokedKey)
def test_gpg_verify_revoked():
    gpg = GnuPG()
    import_key('revoked_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-revoked.asc'), 'rb').read()
    gpg.verify(msg, b'A2A6 C99C A078 0A71 4F3C  2A17 3E67 1C4F 8C1A 99ED')

@raises(ExpiredKey)
def test_gpg_verify_expired():
        gpg = GnuPG()
        import_key('expired_pubkey.asc', gpg.homedir)
        msg = open(get_gpg_file('signed_message-expired.asc'), 'rb').read()
        gpg.verify(msg, b'5256 2F09 247B 3EB0 B977  D46D 19A8 50C0 02BE 9F35')

@raises(SignedWithWrongKey)
def test_gpg_verify_wrong_key():
        gpg = GnuPG()
        import_key('pgpsync_test_suite_pubkey.asc', gpg.homedir)
        import_key('pgpsync_multiple_uids.asc', gpg.homedir)
        msg = open(get_gpg_file('signed_message-valid.asc'), 'rb').read()
        gpg.verify(msg, b'D86B 4D4B B5DF DD37 8B58  D4D3 F121 AC62 3039 6C33')
