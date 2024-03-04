from cv2 import addWeighted, COLOR_BGR2RGB, COLOR_GRAY2RGB, COLOR_RGB2GRAY, cvtColor, imdecode, IMREAD_COLOR
from io import BytesIO
from numpy import asarray, exp, mgrid, sqrt, uint8
from numpy.fft import fft2, fftshift, ifft2
from PIL import Image
from requests import get as req


class Relief:
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

    # Return image relief
    def get(self) -> dict:
        if self.file_id is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to a photo with <code>relief</code>'
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
            gray = cvtColor(img, COLOR_RGB2GRAY)

            try:
                arg_1 = self.args[1].strip()
                arg_2 = self.args[2].strip()
                if arg_1.isdecimal() and arg_2.isdecimal():
                    n = int(arg_1)
                    k = int(arg_2)
                else:
                    n = 30
                    k = 2
            except Exception:
                n = 30
                k = 2

            # Get mask
            y, x = mgrid[0:(gray.shape[0]), 0:(gray.shape[1])]
            t1 = (x - round(gray.shape[1] / 2)) ** 2
            t2 = (y - round(gray.shape[0] / 2)) ** 2
            rad = (t1 + t2) / (n ** 2)
            mask = exp((-sqrt(rad) ** k))

            # Fourier filter
            f = fft2(gray)
            fshift = fftshift(f)
            filtf1 = fshift * mask
            filtf2 = fftshift(filtf1)
            relief = abs(ifft2(filtf2))

            # Relief result
            relief = gray - relief
            relief = relief.astype(uint8)
            relief = cvtColor(relief, COLOR_GRAY2RGB)

            # Draw relief
            res = addWeighted(img, 0.01, relief, 1, 0)

            # Conversion to Byte
            img = Image.fromarray(res)
            try:
                output = BytesIO()
                img.save(output, format='PNG')
                data = output.getvalue()
            except Exception as e:
                self.result['type'] = 'text'
                self.result['send'] = 'Something went wrong'
                self.result['status'] = False
                self.result['err'] = str(e)
                return self.result

            self.result['send'] = data
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Connection error'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
