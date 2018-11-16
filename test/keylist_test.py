# -*- coding: utf-8 -*-
import os
import pytest

from gpgsync.keylist import URLDownloadError, ProxyURLDownloadError, \
    InvalidFingerprints, Keylist, ValidatorMessageQueue, RefresherMessageQueue


# Load an keylist test file
def get_keylist_file_content(filename):
    filename = os.path.join(os.path.abspath('test/keylist_files'), filename)
    return open(filename, 'rb').read()


def test_verifier_message_queue_add_message():
    q = ValidatorMessageQueue()
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
