import sys
sys.path.append("..")

from unittest import mock
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado import websocket
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
import time
import json

from app import TunnelChat


class ChatTest(AsyncHTTPTestCase):
    def get_app(self):
        return TunnelChat()

    def get_protocol(self):
        return "ws"

    def get_new_ioloop(self):
        return IOLoop.instance()  # extra loop for the websocket client

    def setup_chat_users(self):
        url = "/chatsocket"

        with mock.patch("handlers.chat.ChatSocketHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 1'}
            connection1future = websocket.websocket_connect(self.get_url(url), io_loop=self.io_loop)
            self.connection1 = yield connection1future

        with mock.patch("handlers.chat.ChatSocketHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 2'}
            self.connection2 = yield websocket.websocket_connect(self.get_url(url), io_loop=self.io_loop)

        message = yield self.connection1.read_message()
        jmessage = json.loads(message)
        self.assertEqual('joined the chat', jmessage['body'])
        self.assertEqual('User 2', jmessage['from'])

    @gen_test
    def test_user_receives_last_messages(self):
        yield from self.setup_chat_users()

        self.connection2.write_message("check google")

        with mock.patch("handlers.common.MessageHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 3'}
            path = "/messages"
            url = 'http://localhost:%s%s' % (self.get_http_port(), path)
            client = AsyncHTTPClient(self.io_loop)
            last_messages = yield client.fetch(url)

        response = json.loads(last_messages.body.decode("utf8"))
        response = response[-3:]  # discard old history

        self.assertEqual(response[0]['body'], "joined the chat")
        self.assertEqual(response[0]['from'], "User 1")
        self.assertEqual(response[1]['body'], "joined the chat")
        self.assertEqual(response[1]['from'], "User 2")
        self.assertEqual(response[2]['body'], "check google")
        self.assertEqual(response[2]['from'], "User 2")

    @gen_test
    def test_user_receives_users_list(self):
        yield from self.setup_chat_users()

        with mock.patch("handlers.common.UserListHandler.get_current_user") as get_user:
            get_user.return_value = {'name': 'User 2'}
            path = "/userlist"
            url = 'http://localhost:%s%s' % (self.get_http_port(), path)
            client = AsyncHTTPClient(self.io_loop)
            raw_resp = yield client.fetch(url)

        response = json.loads(raw_resp.body.decode("utf8"))

        self.assertEqual(response['current_user'], "User 2")
        self.assertIn("User 1", response['users'])
        self.assertIn("User 2", response['users'])

