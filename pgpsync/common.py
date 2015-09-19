# -*- coding: utf-8 -*-
import os, sys, re, platform
from PyQt5 import QtCore, QtWidgets

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

def get_image_path(filename):
    """
    if platform.system() == 'Linux':
        prefix = os.path.join(sys.prefix, 'share/pgpsync')
    elif platform.system() == 'Windows':
        prefix = os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
    else:
        prefix = os.path.dirname(__file__)
    """
    # Commenting out the path logic until there's proper packaging
    prefix = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'share')

    image_path = os.path.join(prefix, filename)
    return image_path
