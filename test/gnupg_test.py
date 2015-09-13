import os, shutil, subprocess
from nose import with_setup
from pgpsync import GnuPG

gpg_homedir = os.path.abspath('test/homedir')
def get_gpg_file(filename):
    return os.path.join(os.path.abspath('test/gpg_files'), filename)

def setup_func():
    # Delete the gpg homedir if it already exists
    if os.path.exists(gpg_homedir):
        shutil.rmtree(gpg_homedir)

    # Create gpg homedir
    os.mkdir(gpg_homedir, 0700)

    # Import keys
    subprocess.call(['gpg', '--homedir', gpg_homedir, '--import', get_gpg_file('pgpsync_test_suite_pubkey.asc')],
        stderr=subprocess.PIPE, stdout=subprocess.PIPE)

def teardown_func():
    pass

def test_gpg_is_available():
    gpg = GnuPG(homedir=gpg_homedir)
    assert gpg.is_gpg_available()

@with_setup(setup_func, teardown_func)
def test_gpg_recv_key():
    pass

@with_setup(setup_func, teardown_func)
def test_gpg_test_key():
    pass

@with_setup(setup_func, teardown_func)
def test_gpg_get_uid():
    pass

@with_setup(setup_func, teardown_func)
def test_gpg_verify():
    pass
