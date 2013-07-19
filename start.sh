#!/usr/bin/env bash

/usr/bin/redis-server &
/tunnelchat_env/bin/python /tunnelchat/chat.py
