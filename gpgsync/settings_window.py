# -*- coding: utf-8 -*-
import platform
from PyQt5 import QtCore, QtWidgets, QtGui

class SettingsWindow(QtWidgets.QWidget):
    def __init__(self, settings):
        super(SettingsWindow, self).__init__()
        self.setWindowTitle('GPG Sync Settings')
        self.setMinimumWidth(425)
        self.setMaximumWidth(425)
        # self.setMinimumHeight(250)
        # self.setMaximumHeight(250)
        self.settings = settings
        self.settings_layout = SettingsLayout(self.settings)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.settings_layout)
        self.setLayout(layout)

class SettingsLayout(QtWidgets.QVBoxLayout):
    def __init__(self, settings):
        super(SettingsLayout, self).__init__()
        self.settings = settings

        self.run_automatically_checkbox = QtWidgets.QCheckBox("Run GPG Sync automatically on login")
        if self.settings.run_automatically:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Unchecked)

        autostart_vlayout = QtWidgets.QVBoxLayout()
        autostart_vlayout.addWidget(self.run_automatically_checkbox)
        autostart_group = QtWidgets.QGroupBox("Start automatically")
        autostart_group.setLayout(autostart_vlayout)


        self.run_autoupdate_checkbox = QtWidgets.QCheckBox("Check for updates automatically")
        if self.settings.run_autoupdate:
            self.run_autoupdate_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_autoupdate_checkbox.setCheckState(QtCore.Qt.Unchecked)
        # self.run_autoupdate_checkbox.stateChanged.connect(self.run_autoupdate_changed)

        # Update interval
        update_interval_hlayout = QtWidgets.QHBoxLayout()
        update_interval_label = QtWidgets.QLabel('Time between endpoint syncs (in hours)')
        self.update_interval_edit = QtWidgets.QLineEdit()
        self.update_interval_edit.setText(self.settings.update_interval_hours.decode())
        update_interval_hlayout.addWidget(update_interval_label)
        update_interval_hlayout.addWidget(self.update_interval_edit)

        update_interval_group = QtWidgets.QGroupBox("Sync frequency")
        update_interval_group.setLayout(update_interval_hlayout)

        # SOCKS5 proxy settings
        self.use_proxy = QtWidgets.QCheckBox()
        self.use_proxy.setText("Check for updates through SOCKS5 proxy (e.g. Tor)")
        self.use_proxy.setCheckState(QtCore.Qt.Unchecked)

        proxy_host_label = QtWidgets.QLabel('Host')
        self.proxy_host_edit = QtWidgets.QLineEdit()
        self.proxy_host_edit.setText(self.settings.automatic_update_proxy_host.decode())
        proxy_port_label = QtWidgets.QLabel('Port')
        self.proxy_port_edit = QtWidgets.QLineEdit()
        self.proxy_port_edit.setText(self.settings.automatic_update_proxy_port.decode())

        proxy_hlayout = QtWidgets.QHBoxLayout()
        proxy_hlayout.addWidget(proxy_host_label)
        proxy_hlayout.addWidget(self.proxy_host_edit)
        proxy_hlayout.addWidget(proxy_port_label)
        proxy_hlayout.addWidget(self.proxy_port_edit)

        proxy_vlayout = QtWidgets.QVBoxLayout()
        proxy_vlayout.addWidget(self.run_autoupdate_checkbox)
        proxy_vlayout.addWidget(self.use_proxy)
        proxy_vlayout.addLayout(proxy_hlayout)

        autoupdate_group = QtWidgets.QGroupBox("Automatic Updates")
        autoupdate_group.setLayout(proxy_vlayout)

        self.save_btn = QtWidgets.QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)

        self.addWidget(autostart_group)
        self.addWidget(update_interval_group)
        if platform.system() != 'Linux':
            self.addWidget(autoupdate_group)
        self.addWidget(self.save_btn)

    def is_number(self, input):
        try:
            float(input)
            return True
        except ValueError:
            return False

    def save_settings(self):
        self.settings.run_automatically = (self.run_automatically_checkbox.checkState() == QtCore.Qt.Checked)
        if platform.system() != 'Linux':
            self.settings.run_autoupdate = (self.run_autoupdate_checkbox.checkState() == QtCore.Qt.Checked)
            self.settings.automatic_update_use_proxy = (self.use_proxy.checkState() == QtCore.Qt.Checked)
            self.settings.automatic_update_proxy_host = self.proxy_host_edit.text().strip().encode()
            self.settings.automatic_update_proxy_port = self.proxy_port_edit.text().strip().encode()

        # test that the input is actually a number, eventually visually show an error if not
        if self.is_number(self.update_interval_edit.text().strip()):
            self.settings.update_interval_hours = self.update_interval_edit.text().strip().encode()

        self.settings.save()
        # determine if save was successful, close the window if so

