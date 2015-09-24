# -*- coding: utf-8 -*-
import os, sys, re, platform, inspect
from PyQt5 import QtCore, QtWidgets, QtGui

def alert(msg, icon=QtWidgets.QMessageBox.Warning):
    d = QtWidgets.QMessageBox()
    d.setWindowTitle('PGP Sync')
    d.setText(msg)
    d.setIcon(icon)
    d.exec_()

def valid_fp(fp):
    return re.match(b'^[A-F\d]{40}$', clean_fp(fp))

def clean_fp(fp):
    return fp.strip().replace(b' ', b'').upper()

def fp_to_keyid(fp):
    return '0x{}'.format(clean_fp(fp)[-16:].decode()).encode()

def clean_keyserver(keyserver):
    if b'://' not in keyserver:
        return b'hkp://' + keyserver
    return keyserver

def get_resource_path(filename):
    if platform.system() == 'Linux':
        prefix = os.path.join(sys.prefix, 'share/pgpsync')
    elif platform.system() == 'Darwin':
        prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), 'share')

    resource_path = os.path.join(prefix, filename)
    return resource_path

icon = None
def get_icon():
    global icon
    if not icon:
        icon = QtGui.QIcon(get_resource_path('pgpsync.png'))
    return icon

syncing_icon = None
def get_syncing_icon():
    global syncing_icon
    if not syncing_icon:
        syncing_icon = QtGui.QIcon(get_resource_path('syncing.png'))
    return syncing_icon
