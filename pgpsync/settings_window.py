# -*- coding: utf-8 -*-
import os, sys, platform, queue, datetime, requests
from PyQt5 import QtCore, QtWidgets, QtGui

class SettingsWindow(QtWidgets.QWidget):
    def __init__(self, settings):
        super(SettingsWindow, self).__init__()
        self.setWindowTitle('PGP Sync Settings')
        self.setMinimumWidth(400)
        self.settings = settings
        self.settings_layout = SettingsLayout(self.settings)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.settings_layout)
        self.setLayout(layout)

class SettingsLayout(QtWidgets.QVBoxLayout):
    def __init__(self, settings):
        super(SettingsLayout, self).__init__()
        self.settings = settings

        self.run_automatically_checkbox = QtWidgets.QCheckBox("Run PGP Sync automatically on login")
        if self.settings.run_automatically:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Unchecked)
        # self.run_autoupdate_checkbox.stateChanged.connect(self.run_autoupdate_changed)

        self.run_autoupdate_checkbox = QtWidgets.QCheckBox("Check for updates automatically")
        if self.settings.run_autoupdate:
            self.run_autoupdate_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)
        # self.run_autoupdate_checkbox.stateChanged.connect(self.run_autoupdate_changed)

        # Update interval
        update_interval_hlayout = QtWidgets.QHBoxLayout()
        update_interval_label = QtWidgets.QLabel('Update interval (in hours)')
        self.update_interval_edit = QtWidgets.QLineEdit()
        self.update_interval_edit.setText(self.settings.update_interval_hours.decode())
        update_interval_hlayout.addWidget(update_interval_label)
        update_interval_hlayout.addWidget(self.update_interval_edit)
        self.save_btn = QtWidgets.QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)

        self.addWidget(self.run_automatically_checkbox)
        self.addWidget(self.run_autoupdate_checkbox)
        self.addLayout(update_interval_hlayout)
        # self.addWidget(update_interval_label)
        # self.addWidget(self.update_interval_edit)
        self.addWidget(self.save_btn)

    def is_number(self, input):
        try:
            float(input)
            return True
        except ValueError:
            return False

    def save_settings(self):
        self.settings.run_autoupdate = (self.run_autoupdate_checkbox.checkState() == QtCore.Qt.Checked)
        self.settings.run_automatically = (self.run_automatically_checkbox.checkState() == QtCore.Qt.Checked)

        # test that the input is actually a number, eventually visually show an error if not
        if self.is_number(self.update_interval_edit.text().strip()):
            self.settings.update_interval_hours = self.update_interval_edit.text().strip().encode()
        self.settings.save()


