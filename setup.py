#!/usr/bin/env python3
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

import os, sys, platform

p = platform.system()
version_file = os.path.join(os.path.dirname(__file__), 'share', 'version')
version = open(version_file).read().strip().lstrip('v')

description = "GPG Sync lets users have up-to-date public keys for all other members of their organization."
long_description = description + " " + "If you're part of an organization that uses GPG internally you might notice that it doesn't scale well. New people join and create new keys and existing people revoke their old keys and transition to new ones. It quickly becomes unwieldy to ensure that everyone has a copy of everyone else's current key, and that old revoked keys get refreshed to prevent users from accidentally using them."

author = 'Micah Lee'
author_email = 'micah.lee@theintercept.com'
url = 'https://github.com/firstlook/gpgsync'
license = 'GPL v3'
keywords = 'gpgsync, pgp, openpgp, gpg, gnupg'

if p == 'Linux':
    from setuptools import setup
    share_files = [
        'share/gpgsync.png',
        'share/syncing.png',
        'share/error.png',
        'share/loading.gif',
        'share/sks-keyservers.netCA.pem',
        'share/sks-keyservers.netCA.pem.asc',
        'share/version'
    ]
    setup(
        name='gpgsync', version=version,
        description=description, long_description=long_description,
        author=author, author_email=author_email,
        url=url, license=license, keywords=keywords,
        packages=['gpgsync'],
        scripts=['install/gpgsync'],
        data_files=[
            (os.path.join(sys.prefix, 'share/applications'), ['install/gpgsync.desktop']),
            (os.path.join(sys.prefix, 'share/pixmaps'), ['share/gpgsync.png']),
            (os.path.join(sys.prefix, 'share/gpgsync/'), share_files + ['install/gpgsync.desktop'])
        ]
    )

elif p == 'Darwin':
    from cx_Freeze import setup, Executable
    import tempfile

    # Write the correct version into Info.plist
    f = tempfile.NamedTemporaryFile(mode='w')
    custom_info_plist = f.name
    f.write(open('install/Info.plist').read().replace('{VERSION}', str(version)))
    f.flush()

    # Fix cx_Freeze requests bug
    # https://stackoverflow.com/questions/15157502/requests-library-missing-file-after-cx-freeze
    import requests.certs

    setup(
        name='GPG Sync', version=version,
        description=description, long_description=long_description,
        author=author, author_email=author_email,
        url=url, license=license, keywords=keywords,
        options={
            'build_exe': {
                'packages': ['requests'],
                'excludes': [],
                'include_files': [
                    'share',
                    (requests.certs.where(), 'cacert.pem')
                ]
            },
            'bdist_mac': {
                'iconfile': 'install/gpgsync.icns',
                'bundle_name': 'GPG Sync',
                'qt_menu_nib': '/usr/local/Cellar/qt5/5.6.1-1/plugins/platforms',
                'custom_info_plist': custom_info_plist
            }
        },
        executables=[
            Executable('install/gpgsync')
        ]
    )

else:
    print('Unsupported platform')
