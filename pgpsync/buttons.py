# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui

class Buttons(QtWidgets.QVBoxLayout):
    sync_now_signal = QtCore.pyqtSignal(bool)
    quit_signal = QtCore.pyqtSignal()

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
        self.run_automatically_checkbox = QtWidgets.QCheckBox("Run PGP Sync automatically on login")
        if self.settings.run_automatically:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Checked)
        else:
            self.run_automatically_checkbox.setCheckState(QtCore.Qt.Unchecked)
        self.run_automatically_checkbox.stateChanged.connect(self.run_automatically_changed)

        # Next sync label
        self.next_sync_label = QtWidgets.QLabel()
        self.update_next_sync(None)

        # Layout
        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(self.sync_now_btn)
        buttons_layout.addWidget(self.quit_btn)
        self.addLayout(buttons_layout)
        self.addWidget(self.next_sync_label)
        self.addWidget(self.run_automatically_checkbox)

    def sync_now(self):
        self.sync_now_signal.emit(True)

    def quit(self):
        self.quit_signal.emit()

    def update_next_sync(self, remaining_time=None, msg=None):
        if not remaining_time:
            if msg:
                self.next_sync_label.setText(msg)
            else:
                self.next_sync_label.setText("")
            return

        s = int(remaining_time / 1000) # remaining_time is in milliseconds
        minutes = s // 60
        seconds = s - (minutes * 60)

        if minutes > 0:
            next_check = '{} minutes'.format(minutes)
        else:
            next_check = '{} seconds'.format(seconds)

        self.next_sync_label.setText("Next sync check: {}".format(next_check))

    def run_automatically_changed(self, state):
        self.settings.run_automatically = (state == QtCore.Qt.Checked)
        self.settings.save()
