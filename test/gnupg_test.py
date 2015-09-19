# -*- coding: utf-8 -*-
from nose import with_setup
from nose.tools import raises
from pgpsync import *

from .test_helpers import *

def setup_func():
    init_gpg_homedir()

def test_gpg_is_available():
    gpg = GnuPG(homedir=gpg_homedir)
    assert gpg.is_gpg_available()

@with_setup(setup_func)
def test_gpg_recv_key():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.recv_key(b'hkp://keys.gnupg.net', test_key_fp)
    assert gpg.get_uid(test_key_fp) == 'PGP Sync Test Suite Key'

@with_setup(setup_func)
@raises(InvalidKeyserver)
def test_gpg_recv_key_invalid_keyserver():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.recv_key(b'hkp://fakekeyserver', test_key_fp)

@with_setup(setup_func)
@raises(NotFoundOnKeyserver)
def test_gpg_recv_key_not_found_on_keyserver():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.recv_key(b'hkp://keys.gnupg.net', b'0000000000000000000000000000000000000000')

@with_setup(setup_func)
@raises(InvalidFingerprint)
def test_gpg_test_key_invalid_fingerprint():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.test_key(b'deadbeef')

@with_setup(setup_func)
@raises(NotFoundInKeyring)
def test_gpg_test_key_not_found_in_keyring():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.test_key(b'0000000000000000000000000000000000000000')

@with_setup(setup_func)
@raises(RevokedKey)
def test_gpg_test_key_revoked():
    gpg = GnuPG(homedir=gpg_homedir)
    import_key('revoked_pubkey.asc')
    gpg.test_key(b'A2A6 C99C A078 0A71 4F3C  2A17 3E67 1C4F 8C1A 99ED')

@with_setup(setup_func)
@raises(ExpiredKey)
def test_gpg_test_key_expired():
    gpg = GnuPG(homedir=gpg_homedir)
    import_key('expired_pubkey.asc')
    gpg.test_key(b'5256 2F09 247B 3EB0 B977  D46D 19A8 50C0 02BE 9F35')

@with_setup(setup_func)
def test_gpg_get_uid():
    gpg = GnuPG(homedir=gpg_homedir)
    import_key('pgpsync_multiple_uids.asc')
    import_key('pgpsync_test_suite_pubkey.asc')

    # should return the primary uid
    assert gpg.get_uid(b'D86B 4D4B B5DF DD37 8B58  D4D3 F121 AC62 3039 6C33') == 'PGP Sync Test uid 3 <pgpsync-uid3@example.com>'
    assert gpg.get_uid(b'ABCF D99F A161 7E55 B8CD  E5AD E36F D670 7779 47EB') == 'PGP Sync Test Suite Key'

@with_setup(setup_func)
def test_gpg_verify():
    # test a message that works to verify
    gpg = GnuPG(homedir=gpg_homedir)
    import_key('pgpsync_test_suite_pubkey.asc')
    msg = open(get_gpg_file('signed_message-valid.asc'), 'rb').read()
    gpg.verify(msg, b'ABCF D99F A161 7E55 B8CD  E5AD E36F D670 7779 47EB')

@with_setup(setup_func)
@raises(BadSignature)
def test_gpg_verify_invalid_sig():
    # test a message with an invalid sig
    gpg = GnuPG(homedir=gpg_homedir)
    import_key('pgpsync_test_suite_pubkey.asc')
    msg = open(get_gpg_file('signed_message-invalid.asc'), 'rb').read()
    gpg.verify(msg, b'ABCF D99F A161 7E55 B8CD  E5AD E36F D670 7779 47EB')

@with_setup(setup_func)
@raises(RevokedKey)
def test_gpg_verify_revoked():
    gpg = GnuPG(homedir=gpg_homedir)
    import_key('revoked_pubkey.asc')
    msg = open(get_gpg_file('signed_message-revoked.asc'), 'rb').read()
    gpg.verify(msg, b'A2A6 C99C A078 0A71 4F3C  2A17 3E67 1C4F 8C1A 99ED')

@with_setup(setup_func)
@raises(ExpiredKey)
def test_gpg_verify_expired():
        gpg = GnuPG(homedir=gpg_homedir)
        import_key('expired_pubkey.asc')
        msg = open(get_gpg_file('signed_message-expired.asc'), 'rb').read()
        gpg.verify(msg, b'5256 2F09 247B 3EB0 B977  D46D 19A8 50C0 02BE 9F35')

@with_setup(setup_func)
@raises(SignedWithWrongKey)
def test_gpg_verify_wrong_key():
        gpg = GnuPG(homedir=gpg_homedir)
        import_key('pgpsync_test_suite_pubkey.asc')
        import_key('pgpsync_multiple_uids.asc')
        msg = open(get_gpg_file('signed_message-valid.asc'), 'rb').read()
        gpg.verify(msg, b'D86B 4D4B B5DF DD37 8B58  D4D3 F121 AC62 3039 6C33')
