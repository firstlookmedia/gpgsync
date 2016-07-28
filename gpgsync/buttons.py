# -*- coding: utf-8 -*-
import platform
from PyQt5 import QtCore, QtWidgets, QtGui

class Buttons(QtWidgets.QVBoxLayout):
    sync_now_signal = QtCore.pyqtSignal(bool)
    quit_signal = QtCore.pyqtSignal()
    autoupdate_signal = QtCore.pyqtSignal(bool)

    def __init__(self, settings):
        super(Buttons, self).__init__()
        self.settings = settings

        # Sync now button
        self.sync_now_btn = QtWidgets.QPushButton("Sync Now")
        self.sync_now_btn.clicked.connect(self.sync_now)

        # Quit button
        self.quit_btn = QtWidgets.QPushButton("Quit")
        self.quit_btn.clicked.connect(self.quit)

        # Run automatically
        self.run_automatically_checkbox = QtWidgets.QCheckBox("Run GPG Sync automatically on login")
        if self.settings.run_automatically:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.run_automatically_checkbox.stateChanged.connect(self.run_automatically_changed)

        # Check for automatic updates
        self.run_autoupdate_checkbox = QtWidgets.QCheckBox("Check for updates automatically")
        if self.settings.run_autoupdate:
            self.run_autoupdate_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.run_autoupdate_checkbox.stateChanged.connect(self.run_autoupdate_changed)

        # Next sync label
        self.sync_label = QtWidgets.QLabel()
        self.update_sync_label(None)

        # Layout
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.sync_now_btn)
        buttons_layout.addWidget(self.quit_btn)
        self.addLayout(buttons_layout)
        self.addWidget(self.sync_label)
        self.addWidget(self.run_automatically_checkbox)
        if platform.system() != 'Linux':
            self.addWidget(self.run_autoupdate_checkbox)

    def sync_now(self):
        self.sync_now_signal.emit(True)

    def quit(self):
        self.quit_signal.emit()

    def update_sync_label(self, msg=None):
        if msg:
            self.sync_label.setText(msg)
        else:
            self.sync_label.setText("")

    def run_automatically_changed(self, state):
        self.settings.run_automatically = (state == QtCore.Qt.Checked)
        self.settings.save()

    def run_autoupdate_changed(self, state):
        self.settings.run_autoupdate = (state == QtCore.Qt.Checked)
        self.settings.save()
        self.autoupdate_signal.emit((state == QtCore.Qt.Checked))
