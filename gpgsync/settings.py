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
import json
import pickle
import platform
import dateutil.parser as date_parser

from .endpoint import Endpoint


class Settings(object):
    def __init__(self, common):
        self.c = common

        system = platform.system()
        if system == 'Windows':
            appdata = os.environ['APPDATA']
            self.appdata_path = '{0}\\gpgsync'.format(appdata)
        elif system == 'Darwin':
            self.appdata_path = os.path.expanduser("~/Library/Application Support/GPG Sync")
        else:
            self.appdata_path = os.path.expanduser("~/.config/gpgsync")

        self.c.log("Settings", "__init__", "appdata_path: {}".format(self.appdata_path))

        self.load()

    def get_appdata_path(self):
        return self.appdata_path

    def load(self):
        start_new_settings = False
        settings_file = os.path.join(self.appdata_path, 'settings.json')

        # If the settings file exists, load it
        if os.path.isfile(settings_file):
            try:
                # Parse the json file
                self.settings = json.load(open(settings_file, 'r'))
                load_settings = True
                self.c.log("Settings", "load", "settings loaded from {}".format(settings_file))

                # Copy json settings into self
                if 'endpoints' in self.settings:
                    self.endpoints = [Endpoint(self.c).load(e) for e in self.settings['endpoints']]
                else:
                    self.endpoints = []
                if 'run_automatically' in self.settings:
                    self.run_automatically = self.settings['run_automatically']
                else:
                    self.run_automatically = True
                if 'run_autoupdate' in self.settings:
                    self.run_autoupdate = self.settings['run_autoupdate']
                else:
                    self.run_autoupdate = True
                if 'last_update_check' in self.settings:
                    try:
                        self.last_update_check = date_parser.parse(self.settings['last_update_check'])
                    except:
                        self.last_update_check = None
                else:
                    self.last_update_check = None
                if 'last_update_check_err' in self.settings:
                    self.last_update_check_err = self.settings['last_update_check_err']
                else:
                    self.last_update_check_err = False
                if 'update_interval_hours' in self.settings:
                    self.update_interval_hours = str.encode(self.settings['update_interval_hours'])
                else:
                    self.update_interval_hours = b'12'
                if 'automatic_update_use_proxy' in self.settings:
                    self.automatic_update_use_proxy = self.settings['automatic_update_use_proxy']
                else:
                    self.automatic_update_use_proxy = False
                if 'automatic_update_proxy_host' in self.settings:
                    self.automatic_update_proxy_host = str.encode(self.settings['automatic_update_proxy_host'])
                else:
                    self.automatic_update_proxy_host = b'127.0.0.1'
                if 'automatic_update_proxy_port' in self.settings:
                    self.automatic_update_proxy_port = str.encode(self.settings['automatic_update_proxy_port'])
                else:
                    self.automatic_update_proxy_port = b'9050'

                self.configure_run_automatically()

            except:
                self.c.log("Settings", "load", "error loading settings file, starting from scratch")
                print("Error loading settings file, starting from scratch")
                start_new_settings = True

        else:
            self.c.log("Settings", "load", "settings file doesn't exist")

            # Try migrating from old settings
            if not self.migrate_settings_010_011():
                # Nothing to migrate, so start over
                start_new_settings = True

        # Default settings
        if start_new_settings:
            self.endpoints = []
            self.run_automatically = True
            self.run_autoupdate = True
            self.last_update_check = None
            self.last_update_check_err = False
            self.update_interval_hours = b'12'
            self.automatic_update_use_proxy = False
            self.automatic_update_proxy_host = b'127.0.0.1'
            self.automatic_update_proxy_port = b'9050'
            self.save()
            self.configure_run_automatically()

    def save(self):
        self.c.log("Settings", "save")
        self.settings = {
            'endpoints': [e.serialize() for e in self.endpoints],
            'run_automatically': self.run_automatically,
            'run_autoupdate': self.run_autoupdate,
            'last_update_check': self.last_update_check,
            'last_update_check_err': self.last_update_check_err,
            'update_interval_hours': self.update_interval_hours,
            'automatic_update_use_proxy': self.automatic_update_use_proxy,
            'automatic_update_proxy_host': self.automatic_update_proxy_host,
            'automatic_update_proxy_port': self.automatic_update_proxy_port

        }

        if not os.path.exists(self.appdata_path):
            os.makedirs(self.appdata_path)

        with open(os.path.join(self.appdata_path, 'settings.json'), 'w') as settings_file:
            json.dump(self.settings, settings_file, default=self.c.serialize_settings, indent=4)

        self.configure_run_automatically()
        return True

    def configure_run_automatically(self):
        self.c.log("Settings", "configure_run_automatically")

        # TODO: Support Windows
        # Need to copy a shortcut into here on Windows 10:
        # C:\Users\user\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
        # (Is it the same path for Windows 7?)
        # Proably should create the installer first, in order to generate a shortcut.
        # Then, if GPG Sync is installed, this function can copy the shortcut into
        # the right location, or delete the shortcut.

        autorun_dir = None
        if platform.system() == 'Darwin':
            share_filename = 'org.firstlook.gpgsync.plist'
            autorun_dir = os.path.expanduser("~/Library/LaunchAgents")
        elif platform.system() == 'Linux':
            share_filename = 'gpgsync.desktop'
            autorun_dir = os.path.expanduser("~/.config/autostart")

        if autorun_dir:
            if not os.path.exists(autorun_dir):
                os.makedirs(autorun_dir)

            autorun_filename = os.path.join(autorun_dir, share_filename)

            if self.run_automatically:
                buf = open(self.c.get_resource_path(share_filename)).read()
                open(autorun_filename, 'w').write(buf)
            else:
                if os.path.exists(autorun_filename):
                    os.remove(autorun_filename)


    """
    If necessary, migrate settings from 0.1.0 (in an old location and in pickle
    format) to 0.1.1 (in a new location and in json format). Should only run
    once per user.
    """
    def migrate_settings_010_011(self):
        old_settings_path = os.path.expanduser("~/.gpgsync")
        if os.path.isfile(old_settings_path):
            self.c.log("Settings", "migrate_settings_010_011", "there is an old settings file, converting it to a new one")

            # Open it, and modify it to use a different Endpoint object
            # See https://github.com/firstlookmedia/gpgsync/issues/104
            pickle_data = open(old_settings_path, 'rb').read()
            pickle_data = pickle_data.replace(b'gpgsync.endpoint\nEndpoint\n', b'gpgsync.settings\nOldEndpoint\n')

            try:
                # Unpickle the old settings data
                settings = pickle.loads(pickle_data)
                self.c.log("Settings", "migrate_settings_010_011", "settings loaded from {}".format(old_settings_path))

                # Copy pickle settings into self
                if 'endpoints' in settings:
                    self.endpoints = []
                    for old_e in settings['endpoints']:
                        e = Endpoint(self.c)
                        e.verified = old_e.verified
                        e.fingerprint = old_e.fingerprint
                        e.url = old_e.url
                        e.sig_url = old_e.sig_url
                        e.keyserver = old_e.keyserver
                        e.use_proxy = old_e.use_proxy
                        e.proxy_host = old_e.proxy_host
                        e.proxy_port = old_e.proxy_port
                        e.last_checked = old_e.last_checked
                        e.last_synced = old_e.last_synced
                        e.last_failed = old_e.last_failed
                        e.error = old_e.error
                        e.warning = old_e.warning
                        self.endpoints.append(e)
                else:
                    self.endpoints = []
                if 'run_automatically' in settings:
                    self.run_automatically = settings['run_automatically']
                else:
                    self.run_automatically = True
                if 'run_autoupdate' in settings:
                    self.run_autoupdate = settings['run_autoupdate']
                else:
                    self.run_autoupdate = True
                if 'last_update_check' in settings:
                    self.last_update_check = settings['last_update_check']
                else:
                    self.last_update_check = None
                if 'last_update_check_err' in settings:
                    self.last_update_check_err = settings['last_update_check_err']
                else:
                    self.last_update_check_err = False
                if 'update_interval_hours' in settings:
                    self.update_interval_hours = settings['update_interval_hours']
                else:
                    self.update_interval_hours = b'12'
                if 'automatic_update_use_proxy' in settings:
                    self.automatic_update_use_proxy = settings['automatic_update_use_proxy']
                else:
                    self.automatic_update_use_proxy = False
                if 'automatic_update_proxy_host' in settings:
                    self.automatic_update_proxy_host = settings['automatic_update_proxy_host']
                else:
                    self.automatic_update_proxy_host = b'127.0.0.1'
                if 'automatic_update_proxy_port' in settings:
                    self.automatic_update_proxy_port = settings['automatic_update_proxy_port']
                else:
                    self.automatic_update_proxy_port = b'9050'

                # Save the settings into new location, and delete the old settings file
                self.save()
                os.remove(old_settings_path)
                return True
            except:
                self.c.log("Settings", "migrate_settings_010_011", "exception thrown, just start over with settings")
                return False

        return False

"""
This object is never actually used. It's here as a hack to make opening old
GPG Sync settings files, that are in python's pickle format, actually work.
See more: https://github.com/firstlookmedia/gpgsync/issues/104
"""
class OldEndpoint(object):
    def __init__(self):
        self.verified = False
        self.fingerprint = b''
        self.url = b'https://'
        self.sig_url = b'https://.sig'
        self.keyserver = b'hkps://hkps.pool.sks-keyservers.net'
        self.use_proxy = False
        self.proxy_host = b'127.0.0.1'
        self.proxy_port = b'9050'
        self.last_checked = None
        self.last_synced = None
        self.last_failed = None
        self.error = None
        self.warning = None
