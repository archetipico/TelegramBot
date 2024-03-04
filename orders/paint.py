from datetime import datetime
from hashlib import sha1
from re import findall
from requests import get as req
from subprocess import run


class Paint:
    def __init__(self, msg, wd, key, executable):
        self.msg = msg
        self.wd = wd
        self.key = key
        self.executable = executable

        self.hash = sha1((str(msg) + str(datetime.now())).encode()).hexdigest()

        self.result = {
            'type': 'document',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': True,
            'status': True,
            'err': ''
        }

        try:
            # Photo
            self.file_id = msg.reply_to_message.photo[-1].file_id
            self.file_size = msg.reply_to_message.photo[-1].file_size
            self.file_name = 'tmp.jpg'
            self.result['type'] = 'photo'
        except Exception:
            # GIF
            try:
                self.file_id = msg.reply_to_message.document.file_id
                self.file_size = msg.reply_to_message.document.file_size
                self.file_name = msg.reply_to_message.document.file_name
            except Exception:
                # Video
                try:
                    self.file_id = msg.reply_to_message.video.file_id
                    self.file_size = msg.reply_to_message.video.file_size
                    self.file_name = 'tmp.mp4'
                except Exception:
                    self.file_id = None
                    self.file_size = None
                    self.file_name = None

        # If file exists, look at its format
        if self.file_name is not None:
            matches = findall('(?<=\.)[a-zA-Z0-9]+$', self.file_name)
            if len(matches) != 1:
                self.exten = None
            else:
                self.exten = matches[0].lower()
                self.file_name = '{}.{}'.format(
                    self.hash,
                    self.exten
                )
        # The file could have a mime_type
        else:
            try:
                mime_type = findall('(?<=/).+$', msg.reply_to_message.document.mime_type)[0]
                self.exten = mime_type
                self.file_name = '{}.{}'.format(
                    self.hash,
                    self.exten
                )
            except Exception:
                self.exten = None

        self.fp = '{}/orders/tmp/paint/{}'.format(wd, self.file_name)
        self.args = msg.text.split(' ', 1)

    # Paint
    def get(self) -> dict:
        # Check file and format
        if self.file_id is None or self.exten not in ['gif', 'jpeg', 'jpg', 'png', 'mp4']:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to a photo, a video or a GIF with <code>paint</code>'
            self.result['status'] = False
            return self.result

        # If the document exceeds 2097152 Bytes refuse it
        if self.file_size > 2097152:
            self.result['type'] = 'text'
            self.result['send'] = 'The file is too big'
            self.result['status'] = False
            return self.result

        try:
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)
            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']
            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)

            # Request image
            r = req(path_req, stream=True)
            with open(self.fp, 'wb') as f:
                f.write(r.content)

            # Painting level
            try:
                arg = self.args[1].strip()
                if arg.isdecimal():
                    val = int(arg) % 10
                else:
                    val = 5
            except Exception:
                val = 5

            cmd = '{} -paint {} {}'.format(self.executable, val, self.fp)
            run(cmd.split(), capture_output=True, text=True)
            self.result['send'] = self.fp
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Connection error'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
