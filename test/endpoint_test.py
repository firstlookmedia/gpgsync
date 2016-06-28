# -*- coding: utf-8 -*-
from nose import with_setup
from nose.tools import raises
from pgpsync import *

from .test_helpers import *

def test_fetch_url_valid_url():
    e = Endpoint()
    e.url = b'https://sigbin.org/abcfd99fa1617e55b8cde5ade36fd670777947eb'
    e.fetch_url()

@raises(URLDownloadError)
def test_fetch_url_invalid_url():
    e = Endpoint()
    e.url = b'https://somethingfake'
    e.fetch_url()

@raises(ProxyURLDownloadError)
def test_fetch_url_valid_url_invalid_proxy():
    # Assuming 127.0.0.1:9988 is not a valid SOCKS5 proxy...
    e = Endpoint()
    e.url = b'https://sigbin.org/abcfd99fa1617e55b8cde5ade36fd670777947eb'
    e.use_proxy = True
    e.proxy_host = b'127.0.0.1'
    e.proxy_port = b'9988'
    e.fetch_url()

def test_fetch_url_valid_url_valid_proxy():
    # Assuming you have a system Tor installed listening on 127.0.0.1:9050
    e = Endpoint()
    e.url = b'https://sigbin.org/abcfd99fa1617e55b8cde5ade36fd670777947eb'
    e.use_proxy = True
    e.proxy_host = b'127.0.0.1'
    e.proxy_port = b'9050'
    e.fetch_url()

def test_get_fingerprint_list_valid():
    # None of these should throw exceptions
    e = Endpoint()
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints.asc'))
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints_comments.asc'))
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints_no_whitespace.asc'))
    e.get_fingerprint_list(get_endpoint_file_content('fingerprints_weird_whitespace.asc'))

@raises(InvalidFingerprints)
def test_get_fingerprint_list_invalid_fingerprints():
    e = Endpoint()
    e.get_fingerprint_list(get_endpoint_file_content('invalid_fingerprints.asc'))

@raises(FingerprintsListNotSigned)
def test_get_fingerprint_list_invalid_not_signed():
    e = Endpoint()
    e.get_fingerprint_list(get_endpoint_file_content('invalid_not_signed'))
