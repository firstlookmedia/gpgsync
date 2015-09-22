# -*- coding: utf-8 -*-
import queue
from PyQt5 import QtCore, QtWidgets

from . import common

class SysTray(QtWidgets.QSystemTrayIcon):
    show_signal = QtCore.pyqtSignal()
    refresh_signal = QtCore.pyqtSignal(bool)
    quit_signal = QtCore.pyqtSignal()

    def __init__(self):
        super(SysTray, self).__init__(common.get_icon())
        self.show_text = 'Show PGP Sync'
        self.hide_text = 'Hide PGP Sync'

        # Menu
        self.menu = QtWidgets.QMenu()
        self.show_act = self.menu.addAction(self.show_text)
        self.show_act.triggered.connect(self.clicked_show)
        self.refresh_act = self.menu.addAction('Sync endpoints')
        self.refresh_act.triggered.connect(self.clicked_refresh)
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

    def set_window_show(self, showing):
        if showing:
            self.show_act.setText(self.hide_text)
        else:
            self.show_act.setText(self.show_text)

    def clicked_show(self):
        self.show_signal.emit()

    def clicked_refresh(self):
        self.refresh_signal.emit(True)

    def clicked_quit(self):
        self.quit_signal.emit()
