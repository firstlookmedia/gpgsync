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
import os, json, platform
import dateutil.parser as date_parser
from . import common
from . import version_migrations

from .endpoint import Endpoint

class Settings(object):
    def __init__(self):
        system = platform.system()
        if system == 'Windows':
            appdata = os.environ['APPDATA']
            self.appdata_path = '{0}\\gpgsync'.format(appdata)
        elif system == 'Darwin':
            self.appdata_path = os.path.expanduser("~/Library/Application Support/GPG Sync")
        else:
            self.appdata_path = os.path.expanduser("~/.config/gpgsync")

        self.load()

    def get_appdata_path(self):
        return self.appdata_path

    def load(self):
        load_settings = False
        use_old = False
        settings_file = os.path.join(self.appdata_path, 'settings.json')

        if os.path.isfile(settings_file):
            try:
                self.settings = json.load(open(settings_file, 'r'))
                load_settings = True
            except:
                print("Error loading settings file, starting from scratch")
        else:
            old_settings = version_migrations.update_settings_location()
            if old_settings:
                use_old = True
                load_settings = True
                self.settings = old_settings

        if load_settings:
            if 'endpoints' in self.settings:
                if use_old:
                    self.endpoints = self.settings['endpoints']
                else:
                    self.endpoints = [Endpoint().load(e) for e in self.settings['endpoints']]
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
                    if use_old:
                        self.last_update_check = self.settings['last_update_check']
                    else:
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
                if use_old:
                    self.update_interval_hours = self.settings['update_interval_hours']
                else:
                    self.update_interval_hours = str.encode(self.settings['update_interval_hours'])
            else:
                self.update_interval_hours = b'12'
            if 'automatic_update_use_proxy' in self.settings:
                self.automatic_update_use_proxy = self.settings['automatic_update_use_proxy']
            else:
                self.automatic_update_use_proxy = False
            if 'automatic_update_proxy_host' in self.settings:
                if use_old:
                    self.automatic_update_proxy_host = self.settings['automatic_update_proxy_host']
                else:
                    self.automatic_update_proxy_host = str.encode(self.settings['automatic_update_proxy_host'])
            else:
                self.automatic_update_proxy_host = b'127.0.0.1'
            if 'automatic_update_proxy_port' in self.settings:
                if use_old:
                    self.automatic_update_proxy_port = self.settings['automatic_update_proxy_port']
                else:
                    self.automatic_update_proxy_port = str.encode(self.settings['automatic_update_proxy_port'])
            else:
                self.automatic_update_proxy_port = b'9050'
        else:
            # default settings
            self.endpoints = []
            self.run_automatically = True
            self.run_autoupdate = True
            self.last_update_check = None
            self.last_update_check_err = False
            self.update_interval_hours = b'12'
            self.automatic_update_use_proxy = False
            self.automatic_update_proxy_host = b'127.0.0.1'
            self.automatic_update_proxy_port = b'9050'

        if use_old:
            self.save()

        self.configure_run_automatically()

    def save(self):
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
            json.dump(self.settings, settings_file, default=common.serialize_settings, indent=4)

        self.configure_run_automatically()
        return True

    def configure_run_automatically(self):
        if platform.system() == 'Darwin':
            share_filename = 'org.firstlook.gpgsync.plist'
            autorun_dir = os.path.expanduser("~/Library/LaunchAgents")
        elif platform.system() == 'Linux':
            share_filename = 'gpgsync.desktop'
            autorun_dir = os.path.expanduser("~/.config/autostart")

        if not os.path.exists(autorun_dir):
            os.makedirs(autorun_dir)

        autorun_filename = os.path.join(autorun_dir, share_filename)

        if self.run_automatically:
            buf = open(common.get_resource_path(share_filename)).read()
            open(autorun_filename, 'w').write(buf)
        else:
            if os.path.exists(autorun_filename):
                os.remove(autorun_filename)
