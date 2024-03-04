from cv2 import kmeans, KMEANS_PP_CENTERS, TERM_CRITERIA_EPS, TERM_CRITERIA_MAX_ITER
from io import BytesIO
from numpy import argsort, cumsum, float32, hstack, int_, uint8, unique, zeros
from PIL import Image
from requests import get as req
from skimage import io as ski


class Palette:
    def __init__(self, msg, key):
        self.msg = msg
        self.args = msg.text.split(' ', 1)
        self.key = key
        self.param = 5

        try:
            self.file_id = msg.reply_to_message.document.file_id
        except Exception:
            try:
                self.file_id = msg.reply_to_message.photo[-1].file_id
            except Exception:
                self.file_id = None

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

    # Return color palette
    def palette(self, path: str) -> tuple:
        img = ski.imread(path)[:, :]
        # Subsampling
        img = img[::2, ::2]

        pixels = float32(img.reshape(-1, 3))

        criteria = (TERM_CRITERIA_EPS + TERM_CRITERIA_MAX_ITER, 20, .1)
        flags = KMEANS_PP_CENTERS

        _, labels, palette = kmeans(pixels, self.param, None, criteria, 5, flags)
        _, counts = unique(labels, return_counts=True)

        indices = argsort(counts)[::-1]
        freqs = cumsum(hstack([[0], counts[indices] / float(counts.sum())]))
        rows = int_(img.shape[0] * freqs)

        matches = {c: p for c, p in zip(counts, palette)}
        matches = dict(sorted(matches.items(), reverse=True))
        matches = [v for (k, v) in matches.items()]

        dom_patch = zeros(shape=img.shape, dtype=uint8)
        for i in range(len(rows) - 1):
            dom_patch[rows[i]:rows[i + 1], :, :] += uint8(palette[indices[i]])

        return Image.fromarray(dom_patch), matches

    def get(self) -> dict:
        if self.file_id is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Reply to a photo'
            self.result['status'] = False
            return self.result

        if len(self.args) > 2:
            self.result['type'] = 'text'
            self.result['send'] = 'Reply to a photo with <code>palette n</code>'
            self.result['status'] = False
            return self.result

        if len(self.args) == 2 and not self.args[1].isdigit():
            self.result['type'] = 'text'
            self.result['send'] = 'Reply to a photo with <code>palette n</code>'
            self.result['status'] = False
            return self.result

        if len(self.args) == 2 and self.args[1].isdigit():
            val = int(self.args[1])
            if 0 < val <= 10:
                self.param = val

        try:
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)

            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']
            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)

            try:
                img, colors = self.palette(path_req)
            except Exception:
                self.result['type'] = 'text'
                self.result['send'] = 'I cannot extract {} parameters from this photo'.format(self.param)
                self.result['status'] = False
                return self.result

            try:
                output = BytesIO()
                img.save(output, format='PNG')
                data = output.getvalue()
            except Exception as e:
                self.result['type'] = 'text'
                self.result['send'] = 'Something went wrong during the saving'
                self.result['status'] = False
                self.result['err'] = str(e)
                return self.result

            self.result['send'] = data

            caption = 'Colors:'
            for i in range(0, self.param):
                r, g, b = colors[i]
                caption += '\n<code>{}</code>'.format('%02x%02x%02x' % (round(r), round(g), round(b)))
            self.result['caption'] = caption
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Something went wrong during the conversion'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
