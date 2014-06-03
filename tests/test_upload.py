import sys
sys.path.append("..")

import json
import os.path
from tornado.testing import AsyncHTTPTestCase
from unittest import mock

import settings
from app import TunnelChat

class UploadTest(AsyncHTTPTestCase):
    def get_app(self):
        return TunnelChat()

    def test_upload_files_when_logged_in(self):
        post_data = {'data': 'data:text/plain;base64,aGVsbG8K', 'filename': 'program.bat'}
        body = json.dumps(post_data)
        headers = {'Content-Type': 'text/json; charset=utf-8'}

        with mock.patch("handlers.upload.UploadHandler.get_current_user") as get_current_user:
            get_current_user.return_value = {'name': 'UploadingUser'}
            response = self.fetch("/upload", method="POST",
                              auth_username="test", auth_password="test",
                              headers=headers, body=body)

        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, b"UploadingUser - program.bat")  # this format may change

        final_path = os.path.join(settings.MEDIA_ROOT, "UploadingUser - program.bat")
        with open(final_path, 'r') as f:
            uploaded_contents = f.read()
            self.assertEqual(uploaded_contents, "hello\n")

        os.unlink(final_path)
