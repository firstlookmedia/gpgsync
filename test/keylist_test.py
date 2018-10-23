# -*- coding: utf-8 -*-
import os
import pytest

from gpgsync.keylist import URLDownloadError, ProxyURLDownloadError, \
    InvalidFingerprints, Keylist, ValidatorMessageQueue, RefresherMessageQueue


# Load an keylist test file
def get_keylist_file_content(filename):
    filename = os.path.join(os.path.abspath('test/keylist_files'), filename)
    return open(filename, 'rb').read()
