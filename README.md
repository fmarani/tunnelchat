tunnelchat
==========

Let's just say IM implementations generally suck. Client/Server architectures are hard ground for quick iterations, and web is ubiquitous, let's use that. I really like Hipchat, so this is a clone of it, for now.


code
----

Hey yes i hear you, all the code is in one file... and also no unit-tests. Ugly! Expect exploding code for now.


features
--------

* google auth login
* file upload and sharing
* oembed support
* skype emoticons (http://www.messagemagic.net/emoticons.htm)
* userlist

Todo:
* desktop notifications
* @mentions
* activity leds (and time away)
* long messages truncation
* chat history
* message search
* user status
* slash commands
* uploaded file preview
* mobile client
* api
* github pubsubhubbub subscription for commits, issues, comments and pull requests
http://developer.github.com/v3/repos/hooks/#pubsubhubbub


* code posting
* xmpp compatibility with xhtml visualization

ideas to test:
* message pinning (personal)
* message +1 (shared)
* conversation trees
* hubot integration


install
-------

Using docker:

    cd into the project
    docker build -t chat .
    docker run -p 2111:8888 -i -t chat  # change 2111 with your external port


Normal way:

    apt-get install redis-server
    mkvirtualenv --python=/usr/bin/python3 tunnelchat
    pip install -r requirements.txt
    python app.py
