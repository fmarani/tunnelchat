#!/usr/bin/env python

import logging
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.template
import os.path
import uuid
import urllib
import json
import random
from datetime import datetime
import re

from tornado.options import define, options

from tornado import gen

define("port", default=8888, help="run on the given port", type=int)

loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), "templates"))

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
            (r"/upload", UploadHandler),
            (r"/auth/login", AuthHandler),
            (r"/auth/logout", LogoutHandler),
        ]
        settings = dict(
            cookie_secret="ifjewoijfo32jfoijoiufh23foi2hcfiuh2huhf32iuhcfiu32hci32",
            template_loader=loader,
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            login_url="/auth/login",
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class UserMixin(object):
    def get_current_user(self):
        user_json = self.get_secure_cookie("chat_user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)

class UploadHandler(UserMixin, tornado.web.RequestHandler):
    @tornado.web.authenticated
    def post(self):
        file1 = self.request.files['file'][0]
        original_fname = file1['filename']
        prefix = self.current_user['name']
        final_filename= prefix + " - " + original_fname
        output_file = open("static/uploads/" + final_filename, 'w')
        output_file.write(file1['body'])

        upload_msg = tornado.escape.to_basestring(
            loader.load("upload.html").generate(final_filename=final_filename))
        ChatSocketHandler.new_message(self.current_user['name'], upload_msg, system=True)

        self.finish(final_filename)


class AuthHandler(UserMixin, tornado.web.RequestHandler, tornado.auth.GoogleMixin):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        if self.get_argument("openid.mode", None):
            user = yield self.get_authenticated_user()
            self.set_secure_cookie("chat_user",
                                   tornado.escape.json_encode(user))
            self.redirect("/")
            return
        self.authenticate_redirect()


class LogoutHandler(UserMixin, tornado.web.RequestHandler):
    def get(self):
        # This logs the user out of this demo app, but does not log them
        # out of Google.  Since Google remembers previous authorizations,
        # returning to this app will log them back in immediately with no
        # interaction (unless they have separately logged out of Google in
        # the meantime).
        self.clear_cookie("chat_user")
        self.write('You are now logged out. '
                   'Click <a href="/">here</a> to log back in.')

class MainHandler(UserMixin, tornado.web.RequestHandler):
    @tornado.web.authenticated
    def get(self):
        name = tornado.escape.xhtml_escape(self.current_user["name"])
        self.render("index.html", username=name, messages=ChatSocketHandler.cache)


class ChatSocketHandler(UserMixin, tornado.websocket.WebSocketHandler):
    waiters = set()
    cache = []
    cache_size = 200

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        ChatSocketHandler.waiters.add(self)
        from_user = self.get_current_user()['name']
        logging.info("%s joined the chat", from_user)
        ChatSocketHandler.new_message(from_user, "joined the chat", system=True)

    def on_close(self):
        ChatSocketHandler.waiters.remove(self)
        from_user = self.get_current_user()['name']
        logging.info("%s left the chat", from_user)
        ChatSocketHandler.new_message(from_user, "left the chat", system=True)

    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        from_user = self.get_current_user()['name']
        ChatSocketHandler.new_message(from_user, message)

    @classmethod
    def new_message(cls, from_user, body, system=False):
        if not system:
            body = message_beautify(body)

        chat = {
            "id": str(uuid.uuid4()),
            "from": from_user,
            "when": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "body": body,
            "system": system,
            }
        chat["html"] = tornado.escape.to_basestring(
            loader.load("message.html").generate(message=chat))

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)


OEMBED_HINTS = {
        'youtube.com': 'http://www.youtube.com/oembed?url=%s&format=json',
        'flickr.com/photos': 'http://flickr.com/services/oembed.json?url=%s&maxwidth=800&maxheight=600',
        'http://vimeo.com/': 'http://vimeo.com/api/oembed.json?url=%s&maxwidth=800&maxheight=600',
        'www.amazon.co': 'http://oohembed.com/oohembed/?url=%s&maxwidth=400&maxheight=300',
        'play.spotify.com/track/': 'https://embed.spotify.com/oembed/?url=%s',
        }

_URL_RE = re.compile(r"""\b((?:([\w-]+):(/{1,3})|www[.])(?:(?:(?:[^\s&()]|&amp;|&quot;)*(?:[^!"#$%&'()*+,.:;<=>?@\[\]^`{|}~\s]))|(?:\((?:[^\s&()]|&amp;|&quot;)*\)))+)""")

def message_beautify(body):
    words = body.split(" ")
    final_words = []
    for word in words:
        is_special = False
        if _URL_RE.search(word):
            if any(word.endswith(x) for x in ['.jpg','.png','.gif']):
                word = "<img src='%s'>" % word
                is_special = True
            for hint in OEMBED_HINTS.keys():
                if hint in word:
                    oembed_resp = json.load(urllib.urlopen(OEMBED_HINTS[hint] % body))
                    if oembed_resp.has_key('html'):
                        word = oembed_resp['html']
                        is_special = True
                    else:
                        if oembed_resp['type'] == "photo":
                            word = "<img src='%s'>" % oembed_resp['url']
                            is_special = True
            if not is_special:
                word = "<a href='%s'>%s</a>" % (word, word)
                is_special = True
        if not is_special:
            word = tornado.escape.xhtml_escape(word)
        final_words.append(word)
    return ' '.join(final_words)

def timed_bot():
    body = urllib.urlopen("http://www.iheartquotes.com/api/v1/random").read()
    ChatSocketHandler.new_message("The Bot", body)

def main():
    interval_ms = 15 * 60 * 1000
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    main_loop = tornado.ioloop.IOLoop.instance()
    scheduler = tornado.ioloop.PeriodicCallback(timed_bot, interval_ms, io_loop = main_loop)
    scheduler.start()
    main_loop.start()


if __name__ == "__main__":
    main()
