from datetime import datetime
from hashlib import sha1
from requests import get as req
from subprocess import run


class Pixel:
    def __init__(self, msg, wd, key, executable):
        self.msg = msg
        self.key = key
        self.executable = executable
        self.fp = '{}/orders/tmp/pixel/{}.png'.format(
            wd,
            sha1((str(msg) + str(datetime.now())).encode()).hexdigest()
        )

        # FOTO
        try:
            self.file_id = msg.reply_to_message.photo[-1].file_id
        except Exception:
            try:
                self.file_id = msg.reply_to_message.document.file_id
            except Exception:
                self.file_id = None

        self.args = msg.text.split(' ', 1)
        self.result = {
            'type': 'photo',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': True,
            'status': True,
            'err': ''
        }

    # Pixelize
    def get(self) -> dict:
        # Wrong command or wrong file type
        if self.file_id is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Answer to a photo with <code>pixel</code>'
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

            # Pixelization
            try:
                arg = self.args[1].strip()
                if arg.isdecimal():
                    val = int(arg) % 100
                    if val == 0:
                        val = 50
                else:
                    val = 50
            except Exception:
                val = 50

            scale_val = 100 / val * 100
            cmd = '{} -sample {}% -scale {}% {}'.format(self.executable, val, scale_val, self.fp)
            run(cmd.split(), capture_output=True, text=True)

            # Send
            self.result['send'] = self.fp
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Errore di connessione'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
