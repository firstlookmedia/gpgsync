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
import os, pickle

"""
    Check if old settings file exists – should only run once per user
"""
def update_settings_location():
    OLD_SETTINGS_PATH = os.path.expanduser("~/.gpgsync")

    if os.path.isfile(OLD_SETTINGS_PATH):
        try:
            settings = pickle.load(open(OLD_SETTINGS_PATH, 'rb'))
            return settings
        except:
            return None

    return None
