# -*- coding: utf-8 -*-
"""
GPG Sync
Helps users have up-to-date public keys for everyone in their organization
https://github.com/firstlookmedia/gpgsync
Copyright (C) 2016 First Look Media

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import queue
import threading
import time
import sys
from .keylist import Keylist, RefresherMessageQueue


def worker(common, keylist, force, status):
    """
    Sync a single keylist, to be run in a separate thread
    """
    cancel_q = queue.Queue()

    result = Keylist.refresh(common, cancel_q, keylist, force=force)
    keylist.interpret_result(result)

    status[keylist.id]['result'] = result


def sync(common, force=False):
    """
    Sync all keylists.
    """
    print("GPG Sync {}\n".format(common.version))

    num_keylists = len(common.settings.keylists)

    # Status is a dictionary where keys are the keylist "id", a
    # concatination of the keylist URL and fingerprint
    status = {}
    ids = [] # ordered list of ids

    # Build the status object, and display keylist indexes
    for i in range(num_keylists):
        keylist = common.settings.keylists[i]
        keylist.id = keylist.fingerprint + b':' + keylist.url
        ids.append(keylist.id)
        status[keylist.id] = {
            "index": i,
            "event": None,
            "str": None,
            "result": None,
            "keylist": keylist
        }
        print("[{}] Keylist {}, with authority key {}".format(i, keylist.url.decode(), keylist.fingerprint.decode()))
    print("")

    # Start threads
    threads = []
    for keylist in common.settings.keylists:
        keylist.q = RefresherMessageQueue()

        t = threading.Thread(target=worker, args=(common, keylist, force, status,))
        threads.append(t)
        t.start()

    # Monitor queues for updates
    while True:
        # Process the last event in the LIFO queues
        for keylist in common.settings.keylists:
            try:
                event = keylist.q.get(False)
                if event['status'] == RefresherMessageQueue.STATUS_IN_PROGRESS:
                    status[keylist.id]['event'] = event

            except queue.Empty:
                pass

        # Display
        for id in ids:
            if not status[id]['event']:
                status[id]['str'] = '[{0:d}] Syncing...'.format(status[id]['index'])
            else:
                percent = (status[id]['event']['current_key'] / status[id]['event']['total_keys']) * 100;
                status[id]['str'] = '[{0:d}] {1:d}/{2:d} ({3:d}%)'.format(
                    status[id]['index'],
                    status[id]['event']['current_key'],
                    status[id]['event']['total_keys'],
                    int(percent))
        sys.stdout.write('{}          \r'.format('    '.join([status[id]['str'] for id in ids])))

        # Are all keylists finished syncing?
        done = True
        for id in ids:
            if not status[id]['result']:
                done = False
                break
        if done:
            sys.stdout.write('\n\n')
            break
        else:
            # Wait a bit before checking for updates again
            time.sleep(1)

    # Make sure all threads are finished
    for t in threads:
        t.join()

    # Display the results
    for id in ids:
        result = status[id]['result']
        keylist = status[id]['keylist']

        if result['type'] == 'success':
            if keylist1.warning:
                print("[{0:d}] Sync successful. Warning: {1:s}".format(status[id]['index'], keylist.warning))
            else:
                print("[{0:d}] Sync successful.".format(status[id]['index']))
        elif result['type'] == 'error':
            print("[{0:d}] Sync failed. Error: {1:s}".format(status[id]['index'], keylist.error))
        elif result['type'] == 'cancel':
            print("[{0:d}] Sync canceled.".format(status[id]['index']))
        elif result['type'] == 'skip':
            print("[{0:d}] Sync skipped. (Use --force to force syncing.)".format(status[id]['index']))
        else:
            print("[{0:d}] Unknown problem with sync.".format(status[id]['index']))
