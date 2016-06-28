#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, platform
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

system = platform.system()
version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'share', 'version')
version = open(version_file).read().strip()

description = "PGP Sync lets users have up-to-date public keys for all other members of their organization."

long_description = description + " " + "If you're part of an organization that uses PGP internally you might notice that it doesn't scale well. New people join and create new keys and existing people revoke their old keys and transition to new ones. It quickly becomes unwieldy to ensure that everyone has a copy of everyone else's current key, and that old revoked keys get refreshed to prevent users from accidentally using them."

share_files = [
    'share/pgpsync.png',
    'share/syncing.png',
    'share/error.png',
    'share/loading.gif',
    'share/sks-keyservers.netCA.pem',
    'share/sks-keyservers.netCA.pem.asc',
    'share/version'
]

if system == 'Linux':
    setup(
        name='pgpsync',
        version=version,
        description=description,
        long_description=long_description,
        author='Micah Lee',
        author_email='micah.lee@theintercept.com',
        url='https://github.com/firstlook/pgpsync',
        license="GPL v3",
        keywords='pgpsync, pgp, gpg, gnupg',
        packages=['pgpsync'],
        scripts=['install/pgpsync'],
        data_files=[
            (os.path.join(sys.prefix, 'share/applications'), ['install/pgpsync.desktop']),
            (os.path.join(sys.prefix, 'share/pixmaps'), ['share/pgpsync.png']),
            (os.path.join(sys.prefix, 'share/pgpsync/'), share_files + ['install/pgpsync.desktop'])
        ]
    )
