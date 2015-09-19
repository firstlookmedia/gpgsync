# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtWidgets, QtGui

from . import common

class LoadingAnimation(QtWidgets.QLabel):
    def __init__(self, parent=None):
        QtWidgets.QLabel.__init__(self, parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedWidth(16)
        self.setFixedHeight(16)

        self.movie = QtGui.QMovie(common.get_image_path('loading.gif'), QtCore.QByteArray(), self)
        self.movie.setSpeed(100)
        self.movie.start()
        self.setMovie(self.movie)

        self.show()
