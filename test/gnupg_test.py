# -*- coding: utf-8 -*-
import tempfile, os
from nose import with_setup
from nose.tools import raises
from gpgsync import *
from gpgsync.gnupg import *

from .test_helpers import *

def test_gpg_is_available():
    gpg = GnuPG()
    assert gpg.is_gpg_available()

def test_gpg_recv_key():
    gpg = GnuPG()
    gpg.recv_key(b'hkp://keys.gnupg.net', test_key_fp, False, None, None)
    assert gpg.get_uid(test_key_fp) == 'GPG Sync Unit Test Key (not secure in any way)'

@raises(InvalidKeyserver)
def test_gpg_recv_key_invalid_keyserver():
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
    gpg.test_key(b'79358BDE97F831D6027B8FFBDB2F866200EBDDE9')

@raises(ExpiredKey)
def test_gpg_test_key_expired():
    gpg = GnuPG()
    import_key('expired_pubkey.asc', gpg.homedir)
    gpg.test_key(b'30996DFF545AD6A02462639624C6564F385E35F8')

def test_gpg_get_uid():
    gpg = GnuPG()
    import_key('pgpsync_multiple_uids.asc', gpg.homedir)
    import_key('gpgsync_test_pubkey.asc', gpg.homedir)

    # should return the primary uid
    assert gpg.get_uid(b'D86B 4D4B B5DF DD37 8B58  D4D3 F121 AC62 3039 6C33') == 'PGP Sync Test uid 3 <pgpsync-uid3@example.com>'
    assert gpg.get_uid(b'3B72 C32B 49CB B5BB DD57  440E 1D07 D434 48FB 8382') == 'GPG Sync Unit Test Key (not secure in any way)'

def test_gpg_verify():
    # test a message that works to verify
    gpg = GnuPG()
    import_key('gpgsync_test_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-valid.txt'), 'rb').read()
    msg_sig = open(get_gpg_file('signed_message-valid.txt.sig'), 'rb').read()
    gpg.verify(msg_sig, msg, b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382')

@raises(BadSignature)
def test_gpg_verify_invalid_sig():
    # test a message with an invalid sig
    gpg = GnuPG()
    import_key('gpgsync_test_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-invalid.txt'), 'rb').read()
    msg_sig = open(get_gpg_file('signed_message-invalid.txt.sig'), 'rb').read()
    gpg.verify(msg_sig, msg, b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382')

@raises(RevokedKey)
def test_gpg_verify_revoked():
    gpg = GnuPG()
    import_key('revoked_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-revoked.txt'), 'rb').read()
    msg_sig = open(get_gpg_file('signed_message-revoked.txt.sig'), 'rb').read()
    gpg.verify(msg_sig, msg, b'79358BDE97F831D6027B8FFBDB2F866200EBDDE9')

@raises(ExpiredKey)
def test_gpg_verify_expired():
    gpg = GnuPG()
    import_key('expired_pubkey.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-expired.txt'), 'rb').read()
    msg_sig = open(get_gpg_file('signed_message-expired.txt.sig'), 'rb').read()
    gpg.verify(msg_sig, msg, b'30996DFF545AD6A02462639624C6564F385E35F8')

@raises(SignedWithWrongKey)
def test_gpg_verify_wrong_key():
    gpg = GnuPG()
    import_key('gpgsync_test_pubkey.asc', gpg.homedir)
    import_key('pgpsync_multiple_uids.asc', gpg.homedir)
    msg = open(get_gpg_file('signed_message-valid.txt'), 'rb').read()
    msg_sig = open(get_gpg_file('signed_message-valid.txt.sig'), 'rb').read()
    gpg.verify(msg_sig, msg, b'D86B4D4BB5DFDD378B58D4D3F121AC6230396C33')

def test_gpg_list_all_keyids():
    gpg = GnuPG()

    import_key('gpgsync_test_pubkey.asc', gpg.homedir)
    key1_fp = common.clean_fp(b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382')

    import_key('pgpsync_multiple_uids.asc', gpg.homedir)
    key2_fp = common.clean_fp(b'D86B4D4BB5DFDD378B58D4D3F121AC6230396C33')

    assert gpg.list_all_keyids(key1_fp) == [b'0x1D07D43448FB8382', b'0x1ED9906D2F8FC45D']
    assert gpg.list_all_keyids(key2_fp) == [b'0xF121AC6230396C33', b'0x06D001C585800EF4']

def test_gpg_export_pubkey_to_disk():
    appdata = tempfile.TemporaryDirectory()
    gpg = GnuPG(appdata_path=appdata.name)

    fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'
    filename = gpg.get_pubkey_filename_on_disk(fp)

    # The key should be imported
    import_key('gpgsync_test_pubkey.asc', gpg.homedir)
    assert gpg.get_uid(fp) == 'GPG Sync Unit Test Key (not secure in any way)'

    # The file shouldn't exist yet
    assert os.path.isfile(filename) == False

    # Export the key, now it should exist
    gpg.export_pubkey_to_disk(fp)
    assert os.path.isfile(filename) == True

    appdata.cleanup()

def test_gpg_import_pubkey_from_disk():
    appdata = tempfile.TemporaryDirectory()
    gpg = GnuPG(appdata_path=appdata.name)

    fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'
    filename = gpg.get_pubkey_filename_on_disk(fp)

    # Copy the pubkey into appdata_path
    pubkey = open(get_gpg_file('gpgsync_test_pubkey.asc'), 'r').read()
    open(filename, 'w').write(pubkey)

    # The key shouldn't be imported yet
    assert gpg.get_uid(fp) == ''

    # Import the key, and now it should be there
    gpg.import_pubkey_from_disk(fp)
    assert gpg.get_uid(fp) == 'GPG Sync Unit Test Key (not secure in any way)'

    appdata.cleanup()

def test_gpg_delete_pubkey_from_disk():
    appdata = tempfile.TemporaryDirectory()
    gpg = GnuPG(appdata_path=appdata.name)

    fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'
    filename = gpg.get_pubkey_filename_on_disk(fp)

    # The key should be imported
    import_key('gpgsync_test_pubkey.asc', gpg.homedir)
    assert gpg.get_uid(fp) == 'GPG Sync Unit Test Key (not secure in any way)'

    # The file shouldn't exist yet
    assert os.path.isfile(filename) == False

    # Export the key, now it should exist
    gpg.export_pubkey_to_disk(fp)
    assert os.path.isfile(filename) == True

    # Delete it, and it shouldn't exist again
    gpg.delete_pubkey_from_disk(fp)
    assert os.path.isfile(filename) == False

    appdata.cleanup()
