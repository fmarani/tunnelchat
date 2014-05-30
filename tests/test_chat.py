import sys
sys.path.append("..")

from unittest import mock
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado import websocket
from tornado.ioloop import IOLoop
import time
import json

from app import TunnelChat

class ChatTest(AsyncHTTPTestCase):
    def get_app(self):
        return TunnelChat()

    def get_protocol(self):
        return "ws"

    def get_new_ioloop(self):
        return IOLoop.instance()  # the default Client loop

    @gen_test
    def test_room_registry(self):
        url = "/chatsocket"

        with mock.patch("handlers.chat.ChatSocketHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 1'}
            connection1future = websocket.websocket_connect(self.get_url(url), io_loop=self.io_loop)
            connection1 = yield connection1future

        with mock.patch("handlers.chat.ChatSocketHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 2'}
            connection2 = yield websocket.websocket_connect(self.get_url(url), io_loop=self.io_loop)

        message = yield connection1.read_message()
        jmessage = json.loads(message)
        self.assertEqual('joined the chat', jmessage['body'])
        self.assertEqual('User 2', jmessage['from'])
        """
        message = yield connection2.read_message()
        jmessage = json.loads(message)
        self.assertEqual('joined the chat', jmessage['body'])
        self.assertEqual('User 1', jmessage['from'])
        """
