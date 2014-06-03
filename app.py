#!/usr/bin/env python

import logging
import tornado.ioloop
from tornado.options import options
from tornado.web import Application
import urllib.request, urllib.parse, urllib.error

from handlers.common import MainHandler, MessageHandler, UserListHandler
from handlers.auth import AuthHandler, LogoutHandler, GoogleAuthHandler
from handlers.upload import UploadHandler
from handlers.chat import ChatSocketHandler

import settings

class TunnelChat(Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
            (r"/upload", UploadHandler),
            (r"/messages", MessageHandler),
            (r"/userlist", UserListHandler),
            (r"/auth/login", AuthHandler),
            (r"/auth/login/google", GoogleAuthHandler),
            (r"/auth/logout", LogoutHandler),
            (r'/media/(.*)', tornado.web.StaticFileHandler, {'path': settings.MEDIA_ROOT}),
        ]
        Application.__init__(self, handlers, **settings.tornado_settings)


def timed_bot():
    body = urllib.request.urlopen("http://www.iheartquotes.com/api/v1/random").read()
    ChatSocketHandler.send_message("chat", "The Bot", body)


def main():
    interval_ms = 15 * 60 * 1000
    app = TunnelChat()
    app.listen(options.port)
    main_loop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(timed_bot, interval_ms, io_loop=main_loop)
    scheduler.start()
    main_loop.start()


if __name__ == "__main__":
    logging.info("Starting Tunnelchat...")
    main()
