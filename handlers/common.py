import logging
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.template
import json
from tornado import gen

from .base import UserMixin
from .chat import ChatSocketHandler


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
        self.render("index.html", username=name)


class UserListHandler(UserMixin, tornado.web.RequestHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        ChatSocketHandler.current_users("chat", callback=self.on_userlist)

    def on_userlist(self, response):
        logging.info("%s are the current users", response)
        from_user = self.get_current_user()['name']
        self.write({'current_user': from_user, 'users': response})
        self.finish()


class MessageHandler(UserMixin, tornado.web.RequestHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    def get(self):
        ChatSocketHandler.last_messages("chat", callback=self.on_lastmessages)

    def on_lastmessages(self, response):
        logging.info("%s are the last messages", response)
        # lists are not automatically converted to json
        self.write(json.dumps(response))
        self.finish()
