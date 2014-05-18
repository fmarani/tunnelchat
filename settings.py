import logging
import tornado
import tornado.template
import os
from tornado.options import define, options


# Make filepaths relative to settings.
location = lambda x: os.path.join(os.path.dirname(os.path.abspath(__file__)), x)

define("port", default=8888, help="run on the given port", type=int)
define("redis", default="127.0.0.1:6379", help="redis server address")
define("config", default=None, help="tornado config file")
define("debug", default=False, help="debug mode")
tornado.options.parse_command_line()

STATIC_ROOT = location('static')
TEMPLATE_ROOT = location('templates')


settings = {}
settings['debug'] = options.debug
settings['static_path'] = STATIC_ROOT
settings['cookie_secret'] = "your-cookie-secret"
settings['template_loader'] = tornado.template.Loader(TEMPLATE_ROOT)
settings['login_url'] = "/auth/login"

if options.config:
    tornado.options.parse_config_file(options.config)
