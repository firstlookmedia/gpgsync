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
import os
import sys
import signal
import argparse

from .common import Common


def main():
    # https://stackoverflow.com/questions/15157502/requests-library-missing-file-after-cx-freeze
    if getattr(sys, 'frozen', False):
        os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.path.dirname(sys.executable), 'cacert.pem')

    # Allow Ctrl-C to smoothly quit the program instead of throwing an exception
    # https://stackoverflow.com/questions/42814093/how-to-handle-ctrlc-in-python-app-with-pyqt
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Parse arguments
    parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=48))
    parser.add_argument('--debug', action='store_true', dest='debug', help="Log debug output to stdout")
    parser.add_argument('--sync', action='store_true', dest='sync', help="Sync all keylists without loading the GUI")
    args = parser.parse_args()

    debug = args.debug
    sync = args.sync

    # Create the common object
    common = Common(debug)

    # If we only want to sync keylists
    if sync:
        print("not implemented yet")

    else:
        # Otherwise, start the GUI
        from . import gui
        gui.main(common)

if __name__ == '__main__':
    main()
