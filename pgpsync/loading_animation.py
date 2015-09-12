from PyQt4 import QtCore, QtGui

import common

class LoadingAnimation(QtGui.QLabel):
    def __init__(self, parent=None):
        QtGui.QLabel.__init__(self, parent)

        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setFixedWidth(16)
        self.setFixedHeight(16)

        self.movie = QtGui.QMovie(common.get_image_path('loading.gif'), QtCore.QByteArray(), self)
        self.movie.setCacheMode(QtGui.QMovie.CacheAll)
        self.movie.setSpeed(100)
        self.movie.start()
        self.setMovie(self.movie)

        self.show()
