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
import time
import re
import redis

from tornado.options import define, options

from tornado import gen

define("port", default=8888, help="run on the given port", type=int)

loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), "templates"))

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
            (r"/messages", MessageHandler),
            (r"/upload", UploadHandler),
            (r"/userlist", UserListHandler),
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
        self.render("index.html", username=name, messages=ChatSocketHandler.last_messages())


class UserListHandler(UserMixin, tornado.web.RequestHandler):
    @tornado.web.authenticated
    def get(self):
        from_user = self.get_current_user()['name']
        self.write({'current_user': from_user, 'users': ChatSocketHandler.waiters.keys()})

class MessageHandler(UserMixin, tornado.web.RequestHandler):
    @tornado.web.authenticated
    def get(self):
        self.write(json.dumps(list(ChatSocketHandler.last_messages())))

class ChatSocketHandler(UserMixin, tornado.websocket.WebSocketHandler):
    waiters = dict()
    CHAT_STORAGE = "chat"
    redis = redis.StrictRedis('127.0.0.1', 6379)
    cache_size = 30

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        from_user = self.get_current_user()['name']
        if not from_user in ChatSocketHandler.waiters.keys():
            ChatSocketHandler.waiters[from_user] = set()
        ChatSocketHandler.waiters[from_user].add(self)
        logging.info("%s joined the chat", from_user)
        ChatSocketHandler.new_message(from_user, "joined the chat", system=True)

    def on_close(self):
        from_user = self.get_current_user()['name']
        if from_user in ChatSocketHandler.waiters.keys():
            ChatSocketHandler.waiters[from_user].remove(self)
        logging.info("%s left the chat", from_user)
        ChatSocketHandler.new_message(from_user, "left the chat", system=True)

    @classmethod
    def update_cache(cls, chat):
        cls.redis.zadd(cls.CHAT_STORAGE, time.time(), json.dumps(chat))

    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d userwaiters", len(cls.waiters))
        for userwaiters in cls.waiters.values():
            for waiter in userwaiters:
                try:
                    waiter.write_message(chat)
                except:
                    logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        from_user = self.get_current_user()['name']
        ChatSocketHandler.new_message(from_user, message)

    @classmethod
    def last_messages(cls):
        """get last messages"""
        for msg in cls.redis.zrange(cls.CHAT_STORAGE, -cls.cache_size, -1):
            yield json.loads(msg)

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

SMILEYS = {u':(': u'Crying face.png',
 u':)': u'Smiley.png',
 u':*': u'Kiss.png',
 u'(wink)': u'Winking smiley.png',
 u'(handshake)': u'Handshake.png',
 u'(muscle)': u'Muscle.png',
 u':#': u'My lips are sealed.png',
 u'(F)': u'Flower.png',
 u'I=)': u'Sleepy.png',
 u':?': u'Thinking.png',
 u'(devil)': u'Devil.png',
 u'(d)': u'Drink.png',
 u'(h)': u'Heart.png',
 u'B=)': u'Cool smiley.png',
 u'\\o/': u'Dancing.png',
 u'(envy)': u'Envy.png',
 u':=s': u'Worried.png',
 u'(talk)': u'Talking.png',
 u'B-)': u'Cool smiley.png',
 u'(dull)': u'Dull.png',
 u']:)': u'Evil grin.png',
 u'(laugh)': u'Big smiley.png',
 u'(N)': u'No.png',
 u'&gt;:)': u'Evil grin.png',
 u'(rock)': u'Rock.png',
 u'(mooning)': u'Mooning.png',
 u'(yawn)': u'Yawn.png',
 u'($)': u'Cash.png',
 u'(drink)': u'Drink.png',
 u'\\:D/': u'Dancing.png',
 u':o': u'Surprised smiley.png',
 u'(rofl)': u'Rolling on the floor laughing.png',
 u':d': u'Big smiley.png',
 u'B=|': u'Nerdy.png',
 u'(brokenheart)': u'Broken heart.png',
 u':|': u'Speechless smiley.png',
 u'(ninja)': u'Ninja.png',
 u':x': u'My lips are sealed.png',
 u'(wasntme)': u"It wasn't me!.png",
 u'(happy)': u'Happy.png',
 u':&amp;': u'Puking.png',
 u':p': u'Smiley with tongue out.png',
 u'(H)': u'Heart.png',
 u'|(': u'Dull.png',
 u':s': u'Worried.png',
 u'(clock)': u'Time.png',
 u':O': u'Surprised smiley.png',
 u':D': u'Big smiley.png',
 u'(grin)': u'Evil grin.png',
 u'(no)': u'No.png',
 u':@': u'Angry.png',
u'B)': u'Cool smiley.png',
u'(emo)': u'Emo.png',
u'(cake)': u'Cake.png',
u':X': u'My lips are sealed.png',
u'(pi)': u'Pizza.png',
u'(y)': u'Yes.png',
u'(hug)': u'Hug.png',
u'(london)': u'Raining.png',
u':P': u'Smiley with tongue out.png',
u'(mmm)': u'Mmmmm....png',
u'B-|': u'Nerdy.png',
u':S': u'Worried.png',
u'8=|': u'Nerdy.png',
u':=x': u'My lips are sealed.png',
u'8)': u'Cool smiley.png',
u'X-(': u'Angry.png',
u':-O': u'Surprised smiley.png',
u':=|': u'Speechless smiley.png',
u'I-)': u'Sleepy.png',
u'(Y)': u'Yes.png',
u':-@': u'Angry.png',
u':-D': u'Big smiley.png',
u':-X': u'My lips are sealed.png',
u':=o': u'Surprised smiley.png',
u':-S': u'Worried.png',
u':-P': u'Smiley with tongue out.png',
u':-&amp;': u'Puking.png',
u':=d': u'Big smiley.png',
u':=X': u'My lips are sealed.png',
u'(ss)': u'Skype.png',
u':-o': u'Surprised smiley.png',
u'(doh)': u'Doh!.png',
u'(flex)': u'Muscle.png',
u':=S': u'Worried.png',
u':=P': u'Smiley with tongue out.png',
u':-d': u'Big smiley.png',
u'(mo)': u'Cash.png',
u'8-|': u'Nerdy.png',
u':-x': u'My lips are sealed.png',
u':=O': u'Surprised smiley.png',
u':-|': u'Speechless smiley.png',
u':"&gt;': u'Blush.png',
u':-s': u'Worried.png',
u':=@': u'Angry.png',
u'(L)': u'Heart.png',
u':=D': u'Big smiley.png',
u'(mp)': u'Phone.png',
u'(chuckle)': u'Giggle.png',
u'|-()': u'Yawn.png',
u':=?': u'Thinking.png',
u':-p': u'Smiley with tongue out.png',
u'(fubar)': u'FUBAR.png',
u'(blush)': u'Blush.png',
u'(punch)': u'Punch.png',
u':=&amp;': u'Puking.png',
u':=*': u'Kiss.png',
u':=(': u'Crying face.png',
u':=)': u'Smiley.png',
u'8=)': u'Cool smiley.png',
u'8|': u'Nerdy.png',
u':=#': u'My lips are sealed.png',
u';)': u'Winking smiley.png',
u';(': u'Crying face.png',
u':=$': u'Blush.png',
u':-*': u'Kiss.png',
u'\\:d/': u'Dancing.png',
u':-(': u'Crying face.png',
u':-)': u'Smiley.png',
u'8-)': u'Cool smiley.png',
u'(ok)': u'Yes.png',
u':-#': u'My lips are sealed.png',
u'(st)': u'Raining.png',
u':-$': u'Blush.png',
u'(yes)': u'Yes.png',
u'X=(': u'Angry.png',
u':-?': u'Thinking.png',
u'(love)': u'Heart.png',
u'(clap)': u'Clapping.png',
u'(sad)': u'Sad face.png',
u'(swear)': u'Swearing.png',
u'(nod)': u'Nodding.png',
u'(cash)': u'Cash.png',
u'(puke)': u'Puking.png',
u'(inlove)': u'In love.png',
u'(shake)': u'Shake.png',
u'(movie)': u'Movie.png',
u'x=(': u'Angry.png',
u'(music)': u'Music.png',
u'(wait)': u'Wait.png',
u'(bear)': u'Hug.png',
u'(o)': u'Time.png',
u'(kate)': u'Make-up.png',
u'(sun)': u'Sun.png',
u'X(': u'Angry.png',
u'(bandit)': u'Bandit.png',
u'x-(': u'Angry.png',
u'(dance)': u'Dancing.png',
u'(party)': u'Party.png',
u'|=(': u'Dull.png',
u'(smoking)': u'Smoking.png',
u':$': u'Blush.png',
u'(worry)': u'Worried.png',
u'(:|': u'Sweating.png',
u':=p': u'Smiley with tongue out.png',
u'(think)': u'Thinking.png',
u'(drunk)': u'Drunk.png',
u'x(': u'Angry.png',
u'(flower)': u'Flower.png',
u'(heart)': u'Heart.png',
u'(tongueout)': u'Smiley with tongue out.png',
u';=)': u'Winking smiley.png',
u';=(': u'Crying face.png',
u'B|': u'Nerdy.png',
u'(smirk)': u'Smirking.png',
u'(snooze)': u'Sleepy.png',
u'(m)': u'You have mail.png',
u'(cool)': u'Cool smiley.png',
u'(film)': u'Movie.png',
u'(hrv)': u'Pool party.png',
u'(*)': u'Star.png',
u'(time)': u'Time.png',
u'(smoke)': u'Smoking.png',
u'|-(': u'Dull.png',
u'|-)': u'Sleepy.png',
u'(hi)': u'Hi.png',
u'(bug)': u'Bug.png',
u'(mail)': u'You have mail.png',
u'(whew)': u'Whew.png',
u'(beer)': u'Beer.png',
u':^)': u'Wondering.png',
u'(ph)': u'Phone.png',
u'(makeup)': u'Make-up.png',
u'(toivo)': u'Toivo.png',
u'(l)': u'Heart.png',
u'(rain)': u'Raining.png',
u'(mm)': u'Mmmmm....png',
u'(cry)': u'Crying face.png',
u'(D)': u'Drink.png',
u'(ci)': u'Smoking.png',
u'(poolparty)': u'Pool party.png',
u'(mmmm)': u'Mmmmm....png',
u'(call)': u'Call.png',
u'(headbang)': u'Banging head on wall.png',
u'(giggle)': u'Giggle.png',
u'(finger)': u'Finger.png',
u'(pizza)': u'Pizza.png',
u'(sweat)': u'Sweating.png',
u'(~)': u'Movie.png',
u'(angry)': u'Angry.png',
u'(nerd)': u'Nerdy.png',
u'(e)': u'You have mail.png',
u';-)': u'Winking smiley.png',
u';-(': u'Crying face.png',
u'(kiss)': u'Kiss.png',
u'(wonder)': u'Wondering.png',
u'(speechless)': u'Speechless smiley.png',
u'(u)': u'Broken heart.png',
u'(bow)': u'Bowing.png',
u'(coffee)': u'Coffee.png',
u'(banghead)': u'Banging head on wall.png',
u'(^)': u'Cake.png',
u'(O)': u'Time.png',
u'(tmi)': u'Too much information.png',
u'(star)': u'Star.png',
u'(surprised)': u'Surprised smiley.png',
u'(skype)': u'Skype.png',
u'(smile)': u'Smiley.png',
u'(n)': u'No.png',
u'(U)': u'Broken heart.png',
u'(f)': u'Flower.png',
u'(phone)': u'Phone.png',
u'(angel)': u'Angel.png'}

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
        smiley = SMILEYS.get(word, None)
        if smiley:
            word = "<img src='/static/emoticons/%s'/>" % smiley
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
    logging.info("Starting Tunnelchat...")
    main()
