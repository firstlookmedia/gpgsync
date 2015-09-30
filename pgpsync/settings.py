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
            self.endpoints = self.settings['endpoints']
            self.run_automatically = self.settings['run_automatically']
        else:
            # default settings
            self.endpoints = []
            self.run_automatically = True

        self.configure_run_automatically()

    def save(self):
        self.settings = {
            'endpoints': self.endpoints,
            'run_automatically': self.run_automatically
        }
        pickle.dump(self.settings, open(self.settings_path, 'wb'))

        self.configure_run_automatically()

    def configure_run_automatically(self):
        if platform.system() == 'Darwin':
            share_filename = 'org.firstlook.pgpsync.plist'
            autorun_filename = os.path.join(os.path.expanduser("~/Library/LaunchAgents"), share_filename)
        elif platform.system() == 'Linux':
            share_filename = 'pgpsync.desktop'
            autorun_filename = os.path.join(os.path.expanduser("~/.config/autostart"), share_filename)

        if self.run_automatically:
            buf = open(common.get_resource_path(share_filename)).read()
            open(autorun_filename, 'w').write(buf)
        else:
            if os.path.exists(autorun_filename):
                os.remove(autorun_filename)
