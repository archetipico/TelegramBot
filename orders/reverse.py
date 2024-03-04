from datetime import datetime
from hashlib import sha1
from requests import get as req
from re import findall
from subprocess import run


class Reverse:
    def __init__(self, msg, wd, key, executable):
        self.msg = msg
        self.wd = wd
        self.key = key
        self.executable = executable

        self.hash = sha1((str(msg) + str(datetime.now())).encode()).hexdigest()
        self.is_video_note = False
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
                # Sticker
                try:
                    self.file_id = msg.reply_to_message.sticker.file_id
                    self.file_size = msg.reply_to_message.sticker.file_size
                    self.file_name = 'tmp.webm'
                except Exception:
                    # Voice
                    try:
                        self.file_id = msg.reply_to_message.voice.file_id
                        self.file_size = msg.reply_to_message.voice.file_size
                        self.file_name = 'tmp.ogg'
                    except Exception:
                        # Audio
                        try:
                            self.file_id = msg.reply_to_message.audio.file_id
                            self.file_size = msg.reply_to_message.audio.file_size
                            self.file_name = msg.reply_to_message.audio.file_name
                        except Exception:
                            # Bubble video
                            try:
                                self.file_id = msg.reply_to_message.video_note.file_id
                                self.file_size = msg.reply_to_message.video_note.file_size
                                self.file_name = 'tmp.mp4'
                                self.is_video_note = True
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
                mime_type = findall('(?<=\/).+$', msg.reply_to_message.document.mime_type)[0]
                self.exten = mime_type
                self.file_name = '{}.{}'.format(
                    self.hash,
                    self.exten
                )
            except Exception:
                self.exten = None

        self.fp = '{}/orders/tmp/reverse/{}.{}'.format(
            self.wd,
            self.hash,
            self.exten
        )
        self.args = msg.text.split(' ', 1)

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

    # Execute the command and capture output
    def execute(self, cmd) -> None:
        try:
            run(cmd.split(), capture_output=True, text=True).stdout
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Errore di elaborazione'
            self.result['status'] = False
            self.result['err'] = str(e)
            return self.result

        return

    # Return the reversed file
    def get(self) -> dict:
        # se viene richiesta la lista
        if len(self.args) == 2 and self.args[1] == '-l':
            self.result['type'] = 'text'
            self.result['send'] = '''
Valid extensions:
<code>gif</code>
<code>mov</code>
<code>mp3</code>
<code>mp4</code>
<code>ogg</code>
<code>webm</code>
        '''
            return self.result

        # If the command is wrong
        if self.file_id is None or self.file_size is None or self.file_name is None or len(self.args) != 1:
            self.result['type'] = 'text'
            self.result['send'] = ('Answer to a valid file type with <code>rev</code>, type <code>rev '
                                   '-l</code> for the list of supported file types')
            self.result['status'] = False
            return self.result

        # Accepted files and maximum file sizes (in Byte)
        specifications = {
            'gif': 8388608,
            'mov': 4194304,
            'mp3': 26214400,
            'mp4': 4194304,
            'ogg': 26214400,
            'webm': 26214400
        }

        if self.exten not in specifications:
            self.result['type'] = 'text'
            self.result['send'] = ('File type <code>{}</code> not supported, type <code>rev -l</code> to '
                                   'see the list of supported file types').format(self.exten)
            self.result['status'] = False
            return self.result

        # File size is too big
        if self.file_size > specifications.get(self.exten):
            self.result['type'] = 'text'
            self.result['send'] = ('The file is too big: your file weights {} Bytes while the maximum file size '
                                   'for this file type is {} Bytes').format(self.file_size, specifications.get(self.exten))
            self.result['status'] = False
            return self.result

        try:
            # Request file
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)
            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']

            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)
            r = req(path_req, stream=True)
            with open(self.fp, 'wb') as f:
                f.write(r.content)

            try:
                # If it's OGG send as 'voice'
                if self.exten == 'ogg':
                    self.result['type'] = 'voice'

                # If it's WEBM or GIF, convert to MP4
                if self.exten == 'webm':
                    out = '{}/orders/tmp/reverse/{}-out.mp4'.format(
                        self.wd,
                        self.hash
                    )
                    self.execute('{} -y -fflags +genpts -i {} -r 24 {}'.format(self.executable, self.fp, out))

                    self.fp = out
                    out = '{}/orders/tmp/reverse/{}-out.mp4'.format(
                        self.wd,
                        self.hash
                    )
                elif self.exten == 'gif':
                    out = '{}/orders/tmp/reverse/{}-out.mp4'.format(
                        self.wd,
                        self.hash
                    )
                    self.execute('{} -y -i {} -movflags faststart -pix_fmt yuv420p -vf "scale=trunc('
                                 'iw/2)*2:trunc(ih/2)*2" {}'.format(self.executable, self.fp, out))

                    self.fp = out
                    out = '{}/orders/tmp/reverse/{}-out.mp4'.format(
                        self.wd,
                        self.hash
                    )
                else:
                    out = '{}/orders/tmp/reverse/{}-out.{}'.format(
                        self.wd,
                        self.hash,
                        self.exten
                    )

                # Reverse
                self.execute('{} -y -i {} -vf reverse -af areverse {}'.format(self.executable, self.fp, out))
                self.fp = out

                # Convert again to WEBM from MP4 if the file was WEBM (not necessary ofr GIF since it has no audio and it will be sent as GIF automatically)
                if self.exten == 'webm':
                    out = '{}/orders/tmp/reverse/{}-out.webm'.format(
                        self.wd,
                        self.hash
                    )
                    self.execute('{} -y -i {} -vcodec libvpx -cpu-used -5 -deadline realtime -map_metadata -1 '
                                 '-fflags +bitexact -flags:v +bitexact -flags:a +bitexact {}'.format(self.executable, self.fp, out))
                    self.fp = out

                self.result['send'] = self.fp

                if self.is_video_note:
                    self.result['type'] = 'video_note'
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
