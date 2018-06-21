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
import queue
from PyQt5 import QtCore, QtWidgets, QtGui


class StatusBar(QtWidgets.QStatusBar):
    def __init__(self, common):
        super(StatusBar, self).__init__()

        self.c = common

        self.loading_animation = LoadingAnimation(self.c)
        self.loading_animation.hide()
        self.addPermanentWidget(self.loading_animation)

    def show_loading(self):
        self.loading_animation.show()

    def hide_loading(self):
        self.loading_animation.hide()


class MessageQueue(queue.Queue):
    def __init(self):
        super(MessageQueue, self).__init__()

    def add_message(self, msg=None, type='update', timeout=0):
        self.put({
            'type': type,
            'msg': msg,
            'timeout': timeout
        })


class LoadingAnimation(QtWidgets.QLabel):
    def __init__(self, common):
        QtWidgets.QLabel.__init__(self)

        self.c = common

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedWidth(16)
        self.setFixedHeight(16)

        self.movie = QtGui.QMovie(self.c.get_resource_path('loading.gif'), QtCore.QByteArray(), self)
        self.movie.setSpeed(100)
        self.movie.start()
        self.setMovie(self.movie)

        self.show()
