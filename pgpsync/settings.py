# -*- coding: utf-8 -*-
import os, pickle, platform

class Settings(object):
    def __init__(self):
        system = platform.system()
        if system == 'Windows':
            appdata = os.environ['APPDATA']
            self.settings_path = '{0}\\pgpsync'.format(appdata)

        else:
            home = os.path.expanduser("~")
            self.settings_path = '{0}/{1}'.format(home, '.pgpsync')

        self.load()

    def load(self):
        if os.path.isfile(self.settings_path):
            self.settings = pickle.load(open(self.settings_path, 'rb'))
            self.endpoints = self.settings['endpoints']
        else:
            # default settings
            self.endpoints = []

    def save(self):
        self.settings = {
            'endpoints': self.endpoints
        }
        pickle.dump(self.settings, open(self.settings_path, 'wb'))
