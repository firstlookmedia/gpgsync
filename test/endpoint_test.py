# -*- coding: utf-8 -*-
import os
import pytest

from gpgsync.endpoint import URLDownloadError, ProxyURLDownloadError, \
    InvalidFingerprints, Endpoint, VerifierMessageQueue, RefresherMessageQueue


# Load an endpoint test file
def get_endpoint_file_content(filename):
    filename = os.path.join(os.path.abspath('test/endpoint_files'), filename)
    return open(filename, 'rb').read()


def test_fetch_url_valid_url(endpoint):
    endpoint.fetch_url('http://www.example.com/')


def test_fetch_url_invalid_url(endpoint):
    with pytest.raises(URLDownloadError):
        endpoint.fetch_url('https://somethingfake')


def test_fetch_url_valid_url_invalid_proxy(endpoint):
    with pytest.raises(ProxyURLDownloadError):
        # Assuming 127.0.0.1:9988 is not a valid SOCKS5 proxy...
        endpoint.use_proxy = True
        endpoint.proxy_host = b'127.0.0.1'
        endpoint.proxy_port = b'9988'
        endpoint.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')


def test_fetch_url_valid_url_valid_proxy(endpoint):
    # Assuming you have a system Tor installed listening on 127.0.0.1:9050
    endpoint.use_proxy = True
    endpoint.proxy_host = b'127.0.0.1'
    endpoint.proxy_port = b'9050'
    endpoint.fetch_url('https://raw.githubusercontent.com/firstlookmedia/gpgsync/master/fingerprints/fingerprints.txt')


def test_get_fingerprint_list_valid(endpoint):
    # None of these should throw exceptions
    endpoint.get_fingerprint_list(get_endpoint_file_content('fingerprints.txt'))
    endpoint.get_fingerprint_list(get_endpoint_file_content('fingerprints_comments.txt'))
    endpoint.get_fingerprint_list(get_endpoint_file_content('fingerprints_no_whitespace.txt'))
    endpoint.get_fingerprint_list(get_endpoint_file_content('fingerprints_weird_whitespace.txt'))


def test_get_fingerprint_list_invalid_fingerprints(endpoint):
    with pytest.raises(InvalidFingerprints):
        endpoint.get_fingerprint_list(get_endpoint_file_content('invalid_fingerprints.txt'))


def test_verifier_message_queue_add_message():
    q = VerifierMessageQueue()
    q.add_message('this is a test', 1)
    q.add_message('another test', 2)
    q.add_message('yet another test', 3)

    assert q.get(False) == {
        'msg': 'yet another test',
        'step': 3
    }
    assert q.get(False) == {
        'msg': 'another test',
        'step': 2
    }
    assert q.get(False) == {
        'msg': 'this is a test',
        'step': 1
    }


def test_refresher_message_queue_add_message():
    q = RefresherMessageQueue()
    q.add_message(RefresherMessageQueue.STATUS_STARTING)
    q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, 10, 2)
    q.add_message(RefresherMessageQueue.STATUS_IN_PROGRESS, 10, 7)

    assert q.get(False) == {
        'status': RefresherMessageQueue.STATUS_IN_PROGRESS,
        'total_keys': 10,
        'current_key': 7
    }
    assert q.get(False) == {
        'status': RefresherMessageQueue.STATUS_IN_PROGRESS,
        'total_keys': 10,
        'current_key': 2
    }
    assert q.get(False) == {
        'status': RefresherMessageQueue.STATUS_STARTING,
        'total_keys': 0,
        'current_key': 0
    }
