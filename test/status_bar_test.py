from nose import with_setup

from pgpsync import StatusBar, MessageQueue
import test_helpers

def test_status_bar_show_loading_animation():
    status_bar = StatusBar()
    status_bar.show_loading()
    assert not status_bar.loading_animation.isHidden()

def test_status_bar_hide_loading_animation():
    status_bar = StatusBar()
    status_bar.hide_loading()
    assert status_bar.loading_animation.isHidden()
