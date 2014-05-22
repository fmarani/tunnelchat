import sys
sys.path.append("..")

from tornado.testing import AsyncHTTPTestCase

from app import TunnelChat

class HomepageTest(AsyncHTTPTestCase):
    def get_app(self):
        return TunnelChat()

    def test_homepage(self):
        response = self.fetch("/", follow_redirects=False)
        self.assertEqual(response.code, 302)

    def test_homepage_when_logged_in(self):
        response = self.fetch("/", auth_username="test", auth_password="test")
        self.assertEqual(response.code, 200)

