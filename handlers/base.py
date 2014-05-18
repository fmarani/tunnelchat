import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.template


class UserMixin(object):
    def get_current_user(self):
        user_json = self.get_secure_cookie("chat_user")
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)

