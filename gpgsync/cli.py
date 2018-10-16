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
from .keylist import Keylist, RefresherMessageQueue

def sync(common, force=False):
    """
    Sync all keylists.
    """
    for keylist in common.settings.keylists:
        print("Syncing keylist {} with authority key {}".format(keylist.url.decode(), keylist.fingerprint.decode()))

        keylist.q = RefresherMessageQueue()
        cancel_q = queue.Queue()

        result = Keylist.refresh(common, cancel_q, keylist, force=force)
        keylist.interpret_result(result)

        if result['type'] == 'success':
            if keylist.warning:
                print("Sync successful. Warning: {}".format(keylist.warning))
            else:
                print("Sync successful.")
        elif result['type'] == 'error':
            print("Sync failed. Error: {}".format(keylist.error))
        elif result['type'] == 'cancel':
            print("Sync canceled.")
        elif result['type'] == 'skip':
            print("Sync skipped. (Use --force to force syncing.)")
        else:
            print("Unknown problem with sync.")

        print("")
