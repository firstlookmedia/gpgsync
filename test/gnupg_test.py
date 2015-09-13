import os, shutil, subprocess
from nose import with_setup
from nose.tools import raises
from pgpsync import GnuPG, InvalidFingerprint, InvalidKeyserver, NotFoundOnKeyserver, NotFoundInKeyring, RevokedKey, ExpiredKey, VerificationError

test_key_fp = 'ABCFD99FA1617E55B8CDE5ADE36FD670777947EB'
gpg_homedir = os.path.abspath('test/homedir')
def get_gpg_file(filename):
    return os.path.join(os.path.abspath('test/gpg_files'), filename)
def import_test_key():
    subprocess.call(['gpg', '--homedir', gpg_homedir, '--import', get_gpg_file('pgpsync_test_suite_pubkey.asc')],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def setup_func():
    # Delete the gpg homedir if it already exists
    if os.path.exists(gpg_homedir):
        shutil.rmtree(gpg_homedir)

    # Create gpg homedir
    os.mkdir(gpg_homedir, 0700)


def test_gpg_is_available():
    gpg = GnuPG(homedir=gpg_homedir)
    assert gpg.is_gpg_available()

@with_setup(setup_func)
def test_gpg_recv_key():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.recv_key('hkp://keys.gnupg.net', test_key_fp)
    assert gpg.get_uid(test_key_fp) == 'PGP Sync Test Suite Key'

@with_setup(setup_func)
@raises(InvalidKeyserver)
def test_gpg_recv_key_invalid_keyserver():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.recv_key('hkp://fakekeyserver', test_key_fp)

@with_setup(setup_func)
@raises(NotFoundOnKeyserver)
def test_gpg_recv_key_not_found_on_keyserver():
    gpg = GnuPG(homedir=gpg_homedir)
    gpg.recv_key('hkp://keys.gnupg.net', '0000000000000000000000000000000000000000')

@with_setup(setup_func)
def test_gpg_test_key():
    pass

@with_setup(setup_func)
def test_gpg_get_uid():
    pass

@with_setup(setup_func)
def test_gpg_verify():
    pass
