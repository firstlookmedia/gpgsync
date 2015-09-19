# -*- coding: utf-8 -*-
import queue
from PyQt5 import QtCore, QtWidgets

from . import common

class SysTray(QtWidgets.QSystemTrayIcon):
    def __init__(self):
        super(SysTray, self).__init__(common.get_icon())

        # Menu
        self.menu = QtWidgets.QMenu('PGP Sync')
        self.show_act = self.menu.addAction('Show PGP Sync')
        self.show_act.triggered.connect(self.clicked_show)
        self.update_act = self.menu.addAction('Check for updates')
        self.update_act.triggered.connect(self.clicked_update)
        self.menu.addSeparator()
        self.quit_act = self.menu.addAction('Quit')
        self.quit_act.triggered.connect(self.clicked_quit)

        self.setContextMenu(self.menu)
        self.activated.connect(self.clicked_activated)

        # Show the systray icon
        self.show()

    def clicked_activated(self, reason):
        if reason == self.Trigger:
            self.clicked_show()

    def clicked_show(self):
        print('show')

    def clicked_update(self):
        print('update')

    def clicked_quit(self):
        print('quit')
