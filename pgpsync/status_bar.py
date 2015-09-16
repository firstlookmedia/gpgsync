import queue
from PyQt5 import QtCore, QtWidgets

from loading_animation import LoadingAnimation
import common

class StatusBar(QtWidgets.QStatusBar):
        def __init__(self):
            super(StatusBar, self).__init__()
            self.loading_animation = LoadingAnimation()
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
