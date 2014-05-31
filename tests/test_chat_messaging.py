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

    def tear_down_chat(self):
        """close websocket connections"""
        self.connection1.close()
        self.connection2.close()

    @gen_test
    def test_user_receives_messages_from_others(self):
        yield from self.setup_chat_users()

        self.connection2.write_message("hey there!")

        message = yield self.connection1.read_message()
        jmessage = json.loads(message)
        self.assertEqual('hey there!', jmessage['body'])
        self.assertEqual('User 2', jmessage['from'])


    @gen_test
    def test_user_receives_smileys_converted_in_html(self):
        yield from self.setup_chat_users()

        self.connection2.write_message(":-)")

        message = yield self.connection1.read_message()
        jmessage = json.loads(message)
        self.assertEqual("<img src='/static/emoticons/Smiley.png'/>", jmessage['body'])
        self.assertEqual('User 2', jmessage['from'])

    @gen_test
    def test_user_receives_links_wrapped_in_ahrefs(self):
        yield from self.setup_chat_users()

        self.connection2.write_message("check this http://www.google.com/")

        message = yield self.connection1.read_message()
        jmessage = json.loads(message)
        self.assertEqual("check this <a href='http://www.google.com/'>", jmessage['body'])
        self.assertEqual('User 2', jmessage['from'])

