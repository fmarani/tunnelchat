import tornado.escape
import json
from .base import UserMixin
from .chat import ChatSocketHandler

class UploadHandler(UserMixin, tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        base64_content = data['data'].split(",")[1]
        original_fname = data['filename']
        prefix = self.current_user['name']
        final_filename= prefix + " - " + original_fname
        output_file = open("media/" + final_filename, 'w')
        output_file.write(base64_content.decode("base64"))

        upload_msg = self.render_string("upload.html", final_filename=final_filename)
        ChatSocketHandler.send_message("chat", self.current_user['name'], upload_msg, system=True)
