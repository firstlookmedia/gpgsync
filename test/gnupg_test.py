# -*- coding: utf-8 -*-
import os
import subprocess
import pytest

from gpgsync.gnupg import GnuPG, InvalidFingerprint, InvalidKeyserver, \
    KeyserverError, NotFoundOnKeyserver, NotFoundInKeyring, RevokedKey, \
    ExpiredKey, VerificationError, BadSignature, SignedWithWrongKey

# Test fingerprint
test_key_fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'

# Load a gpg test file
def get_gpg_file(filename):
    return os.path.join(os.path.abspath('test/gpg_files'), filename)


# Import a key
def import_key(filename, homedir):
    subprocess.call(['gpg', '--homedir', homedir, '--import', get_gpg_file(filename)],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def test_gpg_is_available(common):
    assert common.gpg.is_gpg_available()


def test_gpg_recv_key(common):
    common.gpg.recv_key(b'hkp://keyserver.ubuntu.com', test_key_fp, False, None, None)
    assert common.gpg.get_uid(test_key_fp) == 'GPG Sync Unit Test Key (not secure in any way)'


def test_gpg_recv_key_uses_default_keyserver(common):
    with pytest.raises(InvalidKeyserver):
        common.gpg.recv_key(None, test_key_fp, False, None, None)


def test_gpg_recv_key_invalid_keyserver(common):
    with pytest.raises(KeyserverError):
        common.gpg.recv_key(b'hkp://fakekeyserver', test_key_fp, False, None, None)


def test_gpg_recv_key_not_found_on_keyserver(common):
    with pytest.raises(NotFoundOnKeyserver):
        common.gpg.recv_key(b'hkp://keyserver.ubuntu.com', b'0000000000000000000000000000000000000000', False, None, None)


def test_gpg_test_key_invalid_fingerprint(common):
    with pytest.raises(InvalidFingerprint):
        common.gpg.test_key(b'deadbeef')


def test_gpg_test_key_not_found_in_keyring(common):
    with pytest.raises(NotFoundInKeyring):
        common.gpg.test_key(b'0000000000000000000000000000000000000000')


def test_gpg_test_key_revoked(common):
    with pytest.raises(RevokedKey):
        import_key('revoked_pubkey.asc', common.gpg.homedir)
        common.gpg.test_key(b'79358BDE97F831D6027B8FFBDB2F866200EBDDE9')


def test_gpg_test_key_expired(common):
    with pytest.raises(ExpiredKey):
        import_key('expired_pubkey.asc', common.gpg.homedir)
        common.gpg.test_key(b'30996DFF545AD6A02462639624C6564F385E35F8')


def test_gpg_get_uid(common):
    import_key('pgpsync_multiple_uids.asc', common.gpg.homedir)
    import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)

    # should return the primary uid
    assert common.gpg.get_uid(b'D86B 4D4B B5DF DD37 8B58  D4D3 F121 AC62 3039 6C33') == 'PGP Sync Test uid 3 <pgpsync-uid3@example.com>'
    assert common.gpg.get_uid(b'3B72 C32B 49CB B5BB DD57  440E 1D07 D434 48FB 8382') == 'GPG Sync Unit Test Key (not secure in any way)'


def test_gpg_verify(common):
    # test a message that works to verify
    import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)
    msg = open(get_gpg_file('signed_message-valid.txt'), 'rb').read()
    msg_sig = open(get_gpg_file('signed_message-valid.txt.sig'), 'rb').read()
    common.gpg.verify(msg_sig, msg, b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382')


def test_gpg_verify_invalid_sig(common):
    with pytest.raises(BadSignature):
        # test a message with an invalid sig
        import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)
        msg = open(get_gpg_file('signed_message-invalid.txt'), 'rb').read()
        msg_sig = open(get_gpg_file('signed_message-invalid.txt.sig'), 'rb').read()
        common.gpg.verify(msg_sig, msg, b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382')


def test_gpg_verify_revoked(common):
    with pytest.raises(RevokedKey):
        import_key('revoked_pubkey.asc', common.gpg.homedir)
        msg = open(get_gpg_file('signed_message-revoked.txt'), 'rb').read()
        msg_sig = open(get_gpg_file('signed_message-revoked.txt.sig'), 'rb').read()
        common.gpg.verify(msg_sig, msg, b'79358BDE97F831D6027B8FFBDB2F866200EBDDE9')


def test_gpg_verify_expired(common):
    with pytest.raises(ExpiredKey):
        import_key('expired_pubkey.asc', common.gpg.homedir)
        msg = open(get_gpg_file('signed_message-expired.txt'), 'rb').read()
        msg_sig = open(get_gpg_file('signed_message-expired.txt.sig'), 'rb').read()
        common.gpg.verify(msg_sig, msg, b'30996DFF545AD6A02462639624C6564F385E35F8')


def test_gpg_verify_wrong_key(common):
    with pytest.raises(SignedWithWrongKey):
        import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)
        import_key('pgpsync_multiple_uids.asc', common.gpg.homedir)
        msg = open(get_gpg_file('signed_message-valid.txt'), 'rb').read()
        msg_sig = open(get_gpg_file('signed_message-valid.txt.sig'), 'rb').read()
        common.gpg.verify(msg_sig, msg, b'D86B4D4BB5DFDD378B58D4D3F121AC6230396C33')


def test_gpg_list_all_keyids(common):
    import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)
    key1_fp = common.clean_fp(b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382')

    import_key('pgpsync_multiple_uids.asc', common.gpg.homedir)
    key2_fp = common.clean_fp(b'D86B4D4BB5DFDD378B58D4D3F121AC6230396C33')

    assert common.gpg.list_all_keyids(key1_fp) == [b'0x1D07D43448FB8382', b'0x1ED9906D2F8FC45D']
    assert common.gpg.list_all_keyids(key2_fp) == [b'0xF121AC6230396C33', b'0x06D001C585800EF4']


def test_gpg_export_pubkey_to_disk(common, tmpdir):
    fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'
    filename = common.gpg.get_pubkey_filename_on_disk(fp)

    # The key should be imported
    import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)
    assert common.gpg.get_uid(fp) == 'GPG Sync Unit Test Key (not secure in any way)'

    # The file shouldn't exist yet
    assert os.path.isfile(filename) == False

    # Export the key, now it should exist
    common.gpg.export_pubkey_to_disk(fp)
    assert os.path.isfile(filename) == True


def test_gpg_import_pubkey_from_disk(common, tmpdir):
    fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'
    filename = common.gpg.get_pubkey_filename_on_disk(fp)

    # Copy the pubkey into appdata_path
    pubkey = open(get_gpg_file('gpgsync_test_pubkey.asc'), 'r').read()
    open(filename, 'w').write(pubkey)

    # The key shouldn't be imported yet
    assert common.gpg.get_uid(fp) == ''

    # Import the key, and now it should be there
    common.gpg.import_pubkey_from_disk(fp)
    assert common.gpg.get_uid(fp) == 'GPG Sync Unit Test Key (not secure in any way)'


def test_gpg_delete_pubkey_from_disk(common, tmpdir):
    fp = b'3B72C32B49CBB5BBDD57440E1D07D43448FB8382'
    filename = common.gpg.get_pubkey_filename_on_disk(fp)

    # The key should be imported
    import_key('gpgsync_test_pubkey.asc', common.gpg.homedir)
    assert common.gpg.get_uid(fp) == 'GPG Sync Unit Test Key (not secure in any way)'

    # The file shouldn't exist yet
    assert os.path.isfile(filename) == False

    # Export the key, now it should exist
    common.gpg.export_pubkey_to_disk(fp)
    assert os.path.isfile(filename) == True

    # Delete it, and it shouldn't exist again
    common.gpg.delete_pubkey_from_disk(fp)
    assert os.path.isfile(filename) == False
