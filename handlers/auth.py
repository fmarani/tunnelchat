import logging
import tornado.auth
import tornado.escape
import tornado.web
from tornado import gen

from .base import UserMixin


def authenticate(login, password):
    """dummy function to authenticate"""
    return login == "demo"


class GoogleAuthHandler(UserMixin, tornado.web.RequestHandler, tornado.auth.GoogleMixin):
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


class AuthHandler(UserMixin, tornado.web.RequestHandler):
    def get(self):
        self.render("login.html")

    def post(self):
        login = self.get_argument("login", None)
        password = self.get_argument("password", None)
        if authenticate(login, password):
            user = {"name": login}
            self.set_secure_cookie("chat_user", tornado.escape.json_encode(user))
            self.redirect("/")
        else:
            error_msg = "?error=" + tornado.escape.url_escape("Login incorrect.")
            self.redirect("/auth/login" + error_msg)


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

