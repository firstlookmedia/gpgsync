import Queue
from PyQt4 import QtCore, QtGui

from loading_animation import LoadingAnimation
import common

class StatusBar(QtGui.QStatusBar):
        def __init__(self):
            super(StatusBar, self).__init__()
            self.loading_animation = LoadingAnimation()
            self.loading_animation.hide()
            self.addPermanentWidget(self.loading_animation)

        def show_loading(self):
            self.loading_animation.show()

        def hide_loading(self):
            self.loading_animation.hide()


class MessageQueue(Queue.Queue):
    def __init(self):
        super(MessageQueue, self).__init__()

    def add_message(self, msg=None, type='update'):
        self.put({
            'type': type,
            'msg': msg
        })
