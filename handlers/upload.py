import tornado.escape
import os.path
import json
import settings
from .base import UserMixin
from .chat import ChatSocketHandler
import base64


class UploadHandler(UserMixin, tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body.decode("utf8"))
        base64_content = data['data'].split(",")[1]
        original_fname = data['filename']

        prefix = self.get_current_user()['name']
        final_filename = prefix + " - " + original_fname
        final_path = os.path.join(settings.MEDIA_ROOT, final_filename)

        output_file = open(final_path, 'w')
        raw_data = base64.b64decode(base64_content.encode("utf8"))
        output_file.write(raw_data.decode("utf8"))

        upload_msg = self.render_string("upload.html", final_filename=final_filename).decode("utf8")
        ChatSocketHandler.send_message("chat", self.current_user['name'], upload_msg, system=True)

        self.write(final_filename)
