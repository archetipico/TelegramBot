from cv2 import addWeighted, Canny as CannyAlgorithm, COLOR_BGR2RGB, COLOR_GRAY2RGB, COLOR_RGB2GRAY, cvtColor, \
    GaussianBlur, imdecode, IMREAD_COLOR
from io import BytesIO
from numpy import asarray
from PIL import Image
from requests import get as req


class Canny:
    def __init__(self, msg, key):
        self.msg = msg
        self.key = key

        try:
            self.file_id = msg.reply_to_message.photo[-1].file_id
        except Exception:
            self.file_id = None

        self.args = msg.text.split(' ', 2)
        self.result = {
            'type': 'photo',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Capture edges inside picture
    def get(self) -> dict:
        if self.file_id is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to an image with <code>canny</code>'
            self.result['status'] = False
            return self.result

        try:
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)

            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']
            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)

            # Request image
            r = req(path_req, stream=True)
            img = asarray(bytearray(r.content), dtype="uint8")
            img = imdecode(img, IMREAD_COLOR)
            img = cvtColor(img, COLOR_BGR2RGB)

            # Edge detection
            gray = cvtColor(img, COLOR_RGB2GRAY)
            blur = GaussianBlur(gray, (5, 5), 0)

            # If arguments are detected
            try:
                values = self.args[len(self.args) - 1].strip().split(',', 1)
                arg_1 = values[0].strip()
                arg_2 = values[1].strip()
                if arg_1.isdecimal() and arg_2.isdecimal():
                    threshold_min = int(arg_1)
                    threshold_max = int(arg_2)
                else:
                    threshold_min = 50
                    threshold_max = 150
            except Exception:
                threshold_min = 50
                threshold_max = 150

            edges = CannyAlgorithm(blur, threshold_min, threshold_max)
            edges = cvtColor(edges, COLOR_GRAY2RGB)

            # If -m is inserted then add mask
            try:
                if self.args[1].strip() == '-m':
                    mask_value = 0.5
                else:
                    mask_value = 0.0
            except Exception:
                mask_value = 0.0

            # Draw edges
            res = addWeighted(img, mask_value, edges, 1, 0)

            # Image to bytes
            try:
                img = Image.fromarray(res)
                output = BytesIO()
                img.save(output, format='PNG')
                data = output.getvalue()
            except Exception as e:
                self.result['type'] = 'text'
                self.result['send'] = 'Qualcosa è andato storto'
                self.result['status'] = False
                self.result['err'] = str(e)
                return self.result

            self.result['send'] = data
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Errore di connessione'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
