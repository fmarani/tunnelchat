import sys
sys.path.append("..")

from lib.message import message_beautify
import unittest


class TestMessageBeautifier(unittest.TestCase):

    def test_image_urls_get_expanded_in_html(self):
        resp = message_beautify("hey check this http://dogecoin.com/imgs/dogecoin-300.png !")
        self.assertEqual(resp, "hey check this <img src='http://dogecoin.com/imgs/dogecoin-300.png'> !")

    def test_oembed_objects_are_expanded_correctly(self):
        resp = message_beautify("https://play.spotify.com/track/6PVLfkwBtG50sFw96KXCb6")
        self.assertEqual(resp, """<iframe src="https://embed.spotify.com/?uri=spotify:track:6PVLfkwBtG50sFw96KXCb6" width="300" height="380" frameborder="0" allowtransparency="true"></iframe>""")

    def test_links_are_wrapped_in_ahrefs(self):
        resp = message_beautify("hey check http://www.google.com/")
        self.assertEqual(resp, "hey check <a href='http://www.google.com/'>http://www.google.com/</a>")

    def test_smileys_are_expanded_in_images(self):
        resp = message_beautify("hello (angel)")
        self.assertEqual(resp, "hello <img src='/static/emoticons/Angel.png'/>")
