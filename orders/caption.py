from cv2 import (CAP_PROP_FPS, CAP_PROP_FRAME_COUNT, CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH, COLOR_BGR2RGB,
                 cvtColor, getTextSize, imdecode, IMREAD_COLOR, putText, VideoCapture)
from imutils.video import FileVideoStream
from io import BytesIO
from numpy import frombuffer, uint8
from PIL import Image
from requests import get as req
from textwrap import wrap


class Caption:
    def __init__(self, msg, key, font_params):
        self.msg = msg
        self.key = key
        self.font, self.line_aa = font_params

        try:
            # Photo
            self.file_id = msg.reply_to_message.photo[-1].file_id
            self.file_size = msg.reply_to_message.photo[-1].file_size
            self.file_format = 'photo'
        except Exception:
            # GIF
            try:
                self.file_id = msg.reply_to_message.document.file_id
                self.file_size = msg.reply_to_message.document.file_size
                self.file_format = 'gif'
            except Exception:
                # Video
                try:
                    self.file_id = msg.reply_to_message.video.file_id
                    self.file_size = msg.reply_to_message.video.file_size
                    self.file_format = 'video'
                except Exception:
                    self.file_id = None
                    self.file_size = None
                    self.file_format = None

        # Split the command `cpt` from the remaining text
        self.args = msg.text.split(' ', 1)
        # Check if the first word is '-f', if it is then it will be processed in the "fast way"
        self.fast = 1
        if self.args[1].strip()[:2] == '-f':
            self.args[1] = self.args[1][2:]
            self.fast = 2

        try:
            self.splitted = self.args[1].split(',', 1)
            if len(self.splitted) == 1:
                self.splitted[1] = ''

            self.arg_0 = self.splitted[0].strip().upper()
            self.arg_1 = self.splitted[1].strip().upper()
        except Exception:
            self.splitted = ['', '']

        # Text values
        self.base_height, self.base_width = (720, 1280)
        self.color = (255, 255, 255)
        self.stroke_color = (0, 0, 0)
        self.image_width = None
        self.font_scale = None
        self.thickness = None
        self.image_height = None

        self.result = {
            'type': '',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Draw text on image
    def draw_text(self, img):
        # Thanks to https://github.com/kiosion/ttbt/blob/master/ttbt.py
        t = '' if self.arg_0 == '' else self.arg_0
        b = '' if self.arg_1 == '' else self.arg_1

        (_, def_h), _ = getTextSize('a', self.font, self.font_scale, self.thickness)
        offset = int(def_h * 1.2)
        for line in wrap(t, width=int(img.shape[1] / def_h)):
            (w, h), _ = getTextSize(line, self.font, self.font_scale, self.thickness)
            org = ((img.shape[1] - w) // 2, offset)
            putText(img, line, org, self.font, self.font_scale, self.stroke_color, self.thickness + 2,
                    lineType=self.line_aa)
            putText(img, line, org, self.font, self.font_scale, self.color, self.thickness, lineType=self.line_aa)
            offset += h * 2

        offset = int(img.shape[0] + def_h * 1.8)
        for line in wrap(b, width=int(img.shape[1] / def_h)):
            (w, h), _ = getTextSize(line, self.font, self.font_scale, self.thickness)
            offset -= h * 2
        for line in wrap(b, width=int(img.shape[1] / def_h)):
            (w, h), _ = getTextSize(line, self.font, self.font_scale, self.thickness)
            org = ((img.shape[1] - w) // 2, offset)
            putText(img, line, org, self.font, self.font_scale, self.stroke_color, self.thickness + 2,
                    lineType=self.line_aa)
            putText(img, line, org, self.font, self.font_scale, self.color, self.thickness, lineType=self.line_aa)
            offset += h * 2

        return img

    # Image operation
    def get_image(self, img) -> None:
        try:
            # If I have to skip text
            if self.splitted == ['', '']:
                res = img
            else:
                # Width and height
                self.image_height, self.image_width, _ = img.shape
                self.font_scale = (0.4 + ((self.image_height * self.image_width) / (self.base_height * self.base_width))
                                    * (5.0 - 0.4))
                self.thickness = int(1 + ((self.image_height * self.image_width) / (self.base_height * self.base_width))
                                    * (10 - 1))

                res = self.draw_text(img)

            output = BytesIO()
            res = cvtColor(res, COLOR_BGR2RGB)
            res = Image.fromarray(res)
            res.save(output, format='PNG')
            data = output.getvalue()

            self.result['type'] = 'photo'
            self.result['send'] = data
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Writing error, retry'
            self.result['status'] = False
            self.result['err'] = str(e)

    # Video operation
    def get_gif(self, path) -> dict:
        try:
            cap = VideoCapture(path)
            frame_count = cap.get(CAP_PROP_FRAME_COUNT)
            fps = cap.get(CAP_PROP_FPS)
            video_length = frame_count / fps

            self.image_width = int(cap.get(CAP_PROP_FRAME_WIDTH))
            self.image_height = int(cap.get(CAP_PROP_FRAME_HEIGHT))
            self.font_scale = (0.4 + ((self.image_height * self.image_width) / (self.base_height * self.base_width))
                                * (5.0 - 0.4))
            self.thickness = int(1 + ((self.image_height * self.image_width) / (self.base_height * self.base_width))
                                * (10 - 1))

            del cap

            if frame_count > 300:
                self.result['type'] = 'text'
                self.result['send'] = 'Too many frames'
                self.result['status'] = False
                return self.result

            fvs = FileVideoStream(path).start()
            frames = []
            frame_counter = 0
            while fvs.more():
                frame = fvs.read()

                if frame is None:
                    break

                # Skip one frame every two if '-f' is enabled
                if frame_counter % self.fast == 0:
                    frame = cvtColor(frame, COLOR_BGR2RGB)

                    # If I have to skip text
                    if self.splitted == ['', '']:
                        res = frame
                    else:
                        res = self.draw_text(frame)

                    frames.append(res)

                frame_counter += 1

            output = BytesIO()
            frames = [Image.fromarray(frame) for frame in frames]
            frames[0].save(output, format="GIF", save_all=True, append_images=frames[1:],
                           duration=int(video_length / frame_count * 1000), loop=0)
            frames[0].seek(0)
            data = output.getvalue()

            self.result['type'] = 'animation'
            self.result['send'] = data
            self.result['filename'] = 'caption.gif'
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Something went wrong'
            self.result['status'] = False
            self.result['err'] = str(e)

    # Return the captioned file
    def get(self) -> dict:
        if self.file_id is None or self.file_format is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to a photo or a GIF with <code>cpt up, down</code>'
            self.result['status'] = False
            return self.result

        # If the document exceeds 2097152 Bytes then refuse it
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
            r = req(path_req, stream=True)

            if self.file_format == 'photo':
                img = imdecode(frombuffer(bytearray(r.content), dtype=uint8), IMREAD_COLOR)
                self.get_image(img)
            else:
                try:
                    self.get_gif(path_req)
                except Exception as e:
                    self.result['type'] = 'text'
                    self.result['send'] = 'Something went wrong'
                    self.result['status'] = False
                    self.result['err'] = str(e)
                    return self.result
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Connection error'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
