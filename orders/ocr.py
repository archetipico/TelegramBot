from cv2 import COLOR_BGR2RGB, cvtColor, imdecode, IMREAD_COLOR
from numpy import asarray
from pytesseract import image_to_string
from re import sub
from requests import get as req


class OCR:
    def __init__(self, msg, key):
        self.msg = msg
        self.key = key

        try:
            self.file_id = msg.reply_to_message.photo[-1].file_id
        except Exception:
            self.file_id = None

        self.args = msg.text.split(' ', 2)
        self.result = {
            'type': 'text',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Capture text inside picture
    def get(self) -> dict:
        if len(self.args) == 2 and self.args[1] == '-l':
            self.result['send'] = 'https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html'
            return self.result

        if self.file_id is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to a photo with <code>ocr</code>'
            self.result['status'] = False
            return self.result

        language = 'eng'
        if len(self.args) == 2:
            language = self.args[1]

        try:
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)

            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']
            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)

            # request image
            r = req(path_req, stream=True)
            img = asarray(bytearray(r.content), dtype="uint8")
            img = imdecode(img, IMREAD_COLOR)
            img = cvtColor(img, COLOR_BGR2RGB)
            text = image_to_string(img, lang=language)
            if len(text) > 0:
                self.result['send'] = sub(r'(\n \n){1,}', '', text)
            else:
                self.result['send'] = 'No text found'
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Something went wrong, type <code>ocr -l</code> to check if the language is correct'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
