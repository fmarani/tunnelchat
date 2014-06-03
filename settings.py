import logging
import tornado
import tornado.template
import os
from tornado.options import define, options


# Make filepaths relative to settings.
location = lambda x: os.path.join(os.path.dirname(os.path.abspath(__file__)), x)

# tornado command line options
define("port", default=8888, help="run on the given port", type=int)
define("redis", default="127.0.0.1:6379", help="redis server address")
define("config", default=None, help="tornado config file")
define("debug", default=False, help="debug mode")
tornado.options.parse_command_line()

STATIC_ROOT = location('static')
TEMPLATE_ROOT = location('templates')

# for uploaded assets
MEDIA_ROOT = location('media')

# tornado settings
tornado_settings = {}
tornado_settings['debug'] = options.debug
tornado_settings['static_path'] = STATIC_ROOT
tornado_settings['cookie_secret'] = "your-cookie-secret"
tornado_settings['template_loader'] = tornado.template.Loader(TEMPLATE_ROOT)
tornado_settings['login_url'] = "/auth/login"

if options.config:
    tornado.options.parse_config_file(options.config)
