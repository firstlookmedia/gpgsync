from nose import with_setup
from pgpsync import StatusBar, MessageQueue

def test_status_bar_show_loading_animation():
    status_bar = StatusBar()
    status_bar.show_loading()
    assert not status_bar.loading_animation.isHidden()

def test_status_bar_hide_loading_animation():
    status_bar = StatusBar()
    status_bar.hide_loading()
    assert status_bar.loading_animation.isHidden()

def test_message_queue_add_message():
    q = MessageQueue()
    q.add_message('this is a test')
    q.add_message('another test', timeout=2000)
    q.add_message(type="clear")

    assert q.get(False) == {
        'type': 'update',
        'msg': 'this is a test',
        'timeout': 0
    }
    assert q.get(False) == {
        'type': 'update',
        'msg': 'another test',
        'timeout': 2000
    }
    assert q.get(False) == {
        'type': 'clear',
        'msg': None,
        'timeout': 0
    }
