import logging
from tornado.options import options
import tornado.websocket
import uuid
import json
from datetime import datetime
from toredis import Client

from lib.message import message_beautify
from .base import UserMixin


def chat_userset_key(chat_channel):
    """return key for userset"""
    return chat_channel + "_users"


def chat_lastmessages_key(chat_channel):
    """return key for userset"""
    return chat_channel + "_lastmessages"


class ChatSocketHandler(UserMixin, tornado.websocket.WebSocketHandler):
    cache_size = 30
    commands_client = Client()
    pub_client = Client()

    def open(self):
        # FIXME: make chat_channel dynamic
        self.chat_channel = "chat"

        self.chat_userset = chat_userset_key(self.chat_channel)
        self.from_user = self.get_current_user()['name']

        host, port = options.redis.split(":")
        self.sub_client = Client()
        self.sub_client.connect(host, int(port))
        logging.debug("Opened subscribe connection to redis")

        # first add entered user in user_set, then subscribe to notifications
        def sadd_finished(resp):
            self.sub_client.subscribe(self.chat_channel, callback=self.on_redis_message)
        self.sub_client.sadd(self.chat_userset, self.from_user, callback=sadd_finished)

        logging.info("%s joined the chat", self.from_user)
        ChatSocketHandler.send_message(self.chat_channel, self.from_user, "joined the chat", system=True)

    def on_redis_message(self, msg):
        msg_type, msg_channel, msg = msg
        if msg_type == b"message":
            # write message back to websocket
            self.write_message(json.loads(msg.decode()))

    def on_close(self):
        logging.info("%s left the chat", self.from_user)

        self.sub_client.srem(self.chat_userset, self.from_user)
        ChatSocketHandler.send_message(self.chat_channel, self.from_user, "left the chat", system=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        ChatSocketHandler.send_message(self.chat_channel, self.from_user, message)

    @classmethod
    def update_lastmessages(cls, chat_channel, chat):
        cls.pub_client.lpush(chat_lastmessages_key(chat_channel), json.dumps(chat))
        cls.pub_client.ltrim(chat_lastmessages_key(chat_channel), 0, cls.cache_size)

    @classmethod
    def last_messages(cls, chat_channel, callback):
        """get last messages"""
        if not cls.commands_client.is_connected():
            host, port = options.redis.split(":")
            cls.commands_client.connect(host, int(port))
            logging.debug("Opened commands connection to redis")

        def transform(response):
            json_resp = [json.loads(x) for x in response]
            callback(json_resp[::-1])

        cls.commands_client.lrange(chat_lastmessages_key(chat_channel), 0, cls.cache_size, callback=transform)

    @classmethod
    def current_users(cls, chat_channel, callback):
        """get last messages"""
        if not cls.commands_client.is_connected():
            host, port = options.redis.split(":")
            cls.commands_client.connect(host, int(port))
            logging.debug("Opened commands connection to redis")
        cls.commands_client.smembers(chat_userset_key(chat_channel), callback)

    @classmethod
    def send_message(cls, chat_channel, from_user, body, system=False):
        if not cls.pub_client.is_connected():
            host, port = options.redis.split(":")
            cls.pub_client.connect(host, int(port))
            logging.debug("Opened publish connection to redis")

        if not system:
            body = message_beautify(body)

        chat_msg = {
            "id": str(uuid.uuid4()),
            "from": from_user,
            "when": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "body": body,
            "system": system,
            }

        cls.update_lastmessages(chat_channel, chat_msg)
        logging.debug("Broadcasting message %s", chat_msg)
        cls.pub_client.publish(chat_channel, json.dumps(chat_msg))


