# -*- coding: utf-8 -*-
import os
import pytest

from gpgsync.keylist import URLDownloadError, ProxyURLDownloadError, \
    InvalidFingerprints, LegacyKeylist


# Load an keylist test file
def get_legacy_keylist_file_content(filename):
    filename = os.path.join(os.path.abspath('test/legacy_keylist_files'), filename)
    return open(filename, 'rb').read()


def test_fetch_url_valid_url(legacy_keylist):
    legacy_keylist.fetch_url('http://www.example.com/')


def test_fetch_url_invalid_url(legacy_keylist):
    with pytest.raises(URLDownloadError):
        legacy_keylist.fetch_url('https://somethingfake')


def test_fetch_url_valid_url_invalid_proxy(legacy_keylist):
    with pytest.raises(ProxyURLDownloadError):
        # Assuming 127.0.0.1:9988 is not a valid SOCKS5 proxy...
        legacy_keylist.use_proxy = True
        legacy_keylist.proxy_host = b'127.0.0.1'
        legacy_keylist.proxy_port = b'9988'
        legacy_keylist.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')


def test_fetch_url_valid_url_valid_proxy(legacy_keylist):
    # Assuming you have a system Tor installed listening on 127.0.0.1:9050
    legacy_keylist.use_proxy = True
    legacy_keylist.proxy_host = b'127.0.0.1'
    legacy_keylist.proxy_port = b'9050'
    legacy_keylist.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')


def test_get_fingerprint_list_valid(legacy_keylist):
    # None of these should throw exceptions
    legacy_keylist.get_fingerprint_list(get_legacy_keylist_file_content('fingerprints.txt'))
    legacy_keylist.get_fingerprint_list(get_legacy_keylist_file_content('fingerprints_comments.txt'))
    legacy_keylist.get_fingerprint_list(get_legacy_keylist_file_content('fingerprints_no_whitespace.txt'))
    legacy_keylist.get_fingerprint_list(get_legacy_keylist_file_content('fingerprints_weird_whitespace.txt'))


def test_get_fingerprint_list_invalid_fingerprints(legacy_keylist):
    with pytest.raises(InvalidFingerprints):
        legacy_keylist.get_fingerprint_list(get_legacy_keylist_file_content('invalid_fingerprints.txt'))
