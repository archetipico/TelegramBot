from gtts import gTTS, lang
from io import BytesIO
from json import dumps


class TTS:
    def __init__(self, msg):
        self.msg = msg
        self.args = msg.text.split(' ', 1)

        try:
            self.reply = msg.reply_to_message
        except Exception:
            self.reply = None

        self.result = {
            'type': 'voice',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Return text-to-speech
    def get(self) -> dict:
        langs = lang.tts_langs()
        if len(self.args) == 2 and self.args[1] == '-l':
            self.result['type'] = 'document'
            self.result['send'] = BytesIO(dumps(langs).encode()).getvalue()
            self.result['filename'] = 'langs.json'
            return self.result

        if len(self.args) < 2 and self.reply is None:
            self.result['type'] = 'text'
            self.result['send'] = ('Type <code>tts language text</code> or answer to a message '
                                   'with <code>tts -l</code>')
            self.result['status'] = False
            return self.result

        if self.reply is not None:
            if 'caption=\'' in str(self.msg) or 'caption=\"' in str(self.msg):
                content = self.reply.caption
            else:
                content = self.reply.text

            try:
                language = self.args[1]
                if language not in langs:
                    language = 'en'
            except:
                language = 'en'
        else:
            try:
                language, content = self.args[1].split(' ', 1)
                if language not in langs:
                    language = 'en'
            except Exception as e:
                content = self.args[1]
                language = 'en'

        try:
            tts = gTTS(content, lang=language.lower())
            fp = BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            self.result['send'] = fp
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = ('Something went wrong, type <code>tts -l</code> to check if the language '
                                   'is correct')
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
