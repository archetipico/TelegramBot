from io import BytesIO
from PIL import Image, ImageOps, ImageStat
from requests import get as req


class OLED:
    def __init__(self, msg, key):
        self.msg = msg
        self.key = key

        try:
            self.file_id = msg.reply_to_message.photo[-1].file_id
        except Exception:
            self.file_id = None

        # Maximum 1 argument but I split by n because if len(self.args) == 3 then there's an error
        self.args = msg.text.split(' ')

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

    # Write for an OLED
    def get(self) -> dict:
        if self.file_id is None or (len(self.args) != 1 and len(self.args) != 2):
            self.result['send'] = 'Rispondi ad una foto con <code>oled</code>'
            self.result['status'] = False
            return self.result

        # Check arguments
        try:
            white_thresh = int(self.args[1]) % 256
        except Exception:
            white_thresh = 127

        try:
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)

            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']
            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)

            # Request image
            r = req(path_req, stream=True)
            # Threshold to classify the pixel as white (mode='1' stands for '1-bit color')
            img = Image.open(BytesIO(r.content)).convert('L').point(lambda x: 255 if x > white_thresh else 0, mode='1')

            # Resize
            img.thumbnail((128, 64), Image.LANCZOS)

            # Since we created a thumbnail, it could not be 128x64, so we paste it on a black background
            img_w, img_h = img.size
            w, h = (128, 64)
            whole = Image.new('RGB', (w, h), (0, 0, 0)).convert('L')
            offset = ((w - img_w) // 2, (h - img_h) // 2)
            whole.paste(img, offset)

            # Invert colors if the image is too bright, so if luminosity is higher than 50% + 12.5% = (127 + 32 + 32) = 191
            stat = ImageStat.Stat(whole)
            if stat.mean[0] > 191:
                whole = ImageOps.invert(whole)

            whole = whole.convert('1')

            # Convert to Bytes
            try:
                output = BytesIO()
                whole.save(output, format='PNG')
                data = output.getvalue()
            except Exception as e:
                self.result['type'] = 'text'
                self.result['send'] = 'Something went wrong'
                self.result['status'] = False
                self.result['err'] = str(e)
                return self.result

            self.result['type'] = 'photo'
            self.result['send'] = data
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Connection error'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
