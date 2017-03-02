# -*- coding: utf-8 -*-
from nose import with_setup
from nose.tools import raises
from gpgsync import *

from .test_helpers import *

def test_fetch_url_valid_url():
    e = Endpoint()
    e.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')

@raises(URLDownloadError)
def test_fetch_url_invalid_url():
    e = Endpoint()
    e.fetch_url('https://somethingfake')

@raises(ProxyURLDownloadError)
def test_fetch_url_valid_url_invalid_proxy():
    # Assuming 127.0.0.1:9988 is not a valid SOCKS5 proxy...
    e = Endpoint()
    e.use_proxy = True
    e.proxy_host = b'127.0.0.1'
    e.proxy_port = b'9988'
    e.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')

def test_fetch_url_valid_url_valid_proxy():
    # Assuming you have a system Tor installed listening on 127.0.0.1:9050
    e = Endpoint()
    e.use_proxy = True
    e.proxy_host = b'127.0.0.1'
    e.proxy_port = b'9050'
    e.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')

def test_get_fingerprint_list_valid():
    # None of these should throw exceptions
    e = Endpoint()
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints.txt'))
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints_comments.txt'))
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints_no_whitespace.txt'))
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints_weird_whitespace.txt'))

@raises(InvalidFingerprints)
def test_get_fingerprint_list_invalid_fingerprints():
    e = Endpoint()
    e.get_fingerprint_list(get_endpoint_file_content('invalid_fingerprints.txt'))
