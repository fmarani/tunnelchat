import sys
sys.path.append("..")

from unittest import mock
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado import websocket

from app import TunnelChat

class ChatTest(AsyncHTTPTestCase):
    def get_app(self):
        return TunnelChat()

    def get_protocol(self):
        return "ws"

    @gen_test
    def test_room_registry(self):
        url = "/chatsocket"

        with mock.patch("handlers.chat.ChatSocketHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 1'}
            connection1 = yield websocket.websocket_connect(
                self.get_url(url),
                io_loop=self.io_loop)

        with mock.patch("handlers.chat.ChatSocketHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 2'}
            connection2 = yield websocket.websocket_connect(
                self.get_url(url),
                io_loop=self.io_loop)

        message = yield connection1.read_message()
        message = yield connection2.read_message()

        self.assertEqual('2 just joined the room', message)
