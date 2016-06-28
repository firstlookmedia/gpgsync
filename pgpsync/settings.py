# -*- coding: utf-8 -*-
import os, pickle, platform
from . import common

class Settings(object):
    def __init__(self):
        system = platform.system()
        if system == 'Windows':
            appdata = os.environ['APPDATA']
            self.settings_path = '{0}\\pgpsync'.format(appdata)
        else:
            self.settings_path = os.path.expanduser("~/.pgpsync")

        self.load()

    def load(self):
        if os.path.isfile(self.settings_path):
            self.settings = pickle.load(open(self.settings_path, 'rb'))
            if 'endpoints' in self.settings:
                self.endpoints = self.settings['endpoints']
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
        else:
            # default settings
            self.endpoints = []
            self.run_automatically = True
            self.run_autoupdate = True

        self.configure_run_automatically()

    def save(self):
        self.settings = {
            'endpoints': self.endpoints,
            'run_automatically': self.run_automatically,
            'run_autoupdate': self.run_autoupdate

        }
        pickle.dump(self.settings, open(self.settings_path, 'wb'))

        self.configure_run_automatically()

    def configure_run_automatically(self):
        if platform.system() == 'Darwin':
            share_filename = 'org.firstlook.pgpsync.plist'
            autorun_dir = os.path.expanduser("~/Library/LaunchAgents")
        elif platform.system() == 'Linux':
            share_filename = 'pgpsync.desktop'
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
