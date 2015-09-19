# -*- coding: utf-8 -*-
from nose import with_setup
from nose.tools import raises
from pgpsync import *

from .test_helpers import *

def test_fetch_url_valid_url():
    e = Endpoint()
    e.update(url=b'https://sigbin.org/abcfd99fa1617e55b8cde5ade36fd670777947eb')
    e.fetch_url()

@raises(URLDownloadError)
def test_fetch_url_invalid_url():
    e = Endpoint()
    e.update(url=b'https://somethingfake')
    e.fetch_url()

@raises(URLDownloadError)
def test_fetch_url_valid_url_invalid_proxy():
    # Assuming 127.0.0.1:9988 is not a valid SOCKS5 proxy...
    e = Endpoint()
    e.update(url=b'https://sigbin.org/abcfd99fa1617e55b8cde5ade36fd670777947eb',
        use_proxy=True, proxy_host=b'127.0.0.1', proxy_port=b'9988')
    e.fetch_url()

def test_fetch_url_valid_url_valid_proxy():
    # Assuming you have a system Tor installed listening on 127.0.0.1:9050
    e = Endpoint()
    e.update(url=b'https://sigbin.org/abcfd99fa1617e55b8cde5ade36fd670777947eb',
        use_proxy=True, proxy_host=b'127.0.0.1', proxy_port=b'9050')
    e.fetch_url()

def test_get_fingerprint_list_valid():
    # Test without whitespace, with whitespace, and with whitespace and comments
    pass

def test_get_fingerprint_list_invalid():
    # Test with lines that are not valid fingerprints
    pass
