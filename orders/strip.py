from datetime import datetime
from hashlib import sha1
from re import findall
from requests import get as req
from scour.scour import parse_args, scourXmlFile
from subprocess import run


class Strip:
    def __init__(self, msg, wd, key, executables):
        self.msg = msg
        self.wd = wd
        self.key = key
        self.exiftool, self.ffmpeg, self.gs, self.jpegoptim, self.optipng = executables

        self.hash = sha1((str(msg) + str(datetime.now())).encode()).hexdigest()

        try:
            self.file_id = msg.reply_to_message.document.file_id
            self.file_size = msg.reply_to_message.document.file_size
            self.file_name = msg.reply_to_message.document.file_name
        except Exception:
            try:
                self.file_id = msg.reply_to_message.photo[-1].file_id
                self.file_size = msg.reply_to_message.photo[-1].file_size
                self.file_name = 'tmp.jpg'
            except Exception:
                try:
                    self.file_id = msg.reply_to_message.video.file_id
                    self.file_size = msg.reply_to_message.video.file_size
                    self.file_name = 'tmp.mp4'
                except Exception:
                    try:
                        self.file_id = msg.reply_to_message.sticker.file_id
                        self.file_size = msg.reply_to_message.sticker.file_size
                        self.file_name = 'tmp.webm'
                    except Exception:
                        try:
                            self.file_id = msg.reply_to_message.video_note.file_id
                            self.file_size = msg.reply_to_message.video_note.file_size
                            self.file_name = 'tmp.mp4'
                        except Exception:
                            self.file_id = None
                            self.file_size = None
                            self.file_name = None

        # If the file exists, look at its format
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

        self.fp = '{}/orders/tmp/strip/{}.{}'.format(
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

    # Return the file without metadata
    def get(self) -> dict:
        # Return list if asked
        if len(self.args) == 2 and self.args[1] == '-l':
            self.result['type'] = 'text'
            self.result['send'] = '''
Funzioni:
<code>R     Reduction</code>
<code>O     Obfuscation</code>

Valid Extensions:
<code>doc   O</code>
<code>docx  O</code>
<code>gif   RO</code>
<code>jpeg  RO</code>
<code>jpg   RO</code>
<code>mov   RO</code>
<code>mp4   RO</code>
<code>pdf   RO</code>
<code>png   RO</code>
<code>svg   RO</code>
<code>webm  RO</code>

<i>Bear in mind that, at times, attempting to reduce file size may instead lead to an increase</i>
        '''
            return self.result

        # If the order is wrong
        if self.file_id is None or self.file_size is None or self.file_name is None or len(self.args) != 1:
            self.result['type'] = 'text'
            self.result['send'] = ('Answer to a valid file type with <code>strip</code>, type <code>strip -l</code> to '
                                   'see the list of supported file types')
            self.result['status'] = False
            return self.result

        # Accepted files and maximum file sizes (in Byte)
        specifications = {
            'doc': 26214400,
            'docx': 26214400,
            'gif': 12582912,
            'jpeg': 26214400,
            'jpg': 26214400,
            'mov': 12582912,
            'mp4': 12582912,
            'pdf': 26214400,
            'png': 26214400,
            'svg': 26214400,
            'webm': 26214400
        }

        # File type not supported
        if self.exten not in specifications.keys():
            self.result['type'] = 'text'
            self.result['send'] = ('File type <code>{}</code> not supported, type <code>strip -l</code> to '
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
            self.result['caption'] = ''

            # Request image
            path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(self.key, self.file_id)
            r = req(path_req, stream=True)
            path = r.json()['result']['file_path']

            path_req = 'https://api.telegram.org/file/bot{}/{}'.format(self.key, path)
            r = req(path_req, stream=True)
            with open(self.fp, 'wb') as f:
                f.write(r.content)

            try:
                if self.exten == 'jpg' or self.exten == 'jpeg':
                    self.execute('{} --strip-all --max=72 {}'.format(self.jpegoptim, self.fp))
                if self.exten == 'png':
                    self.execute('{} --strip all -o1 {}'.format(self.optipng, self.fp))
                if self.exten == 'svg':
                    out_svg = scourXmlFile(
                        self.fp,
                        parse_args([
                            '--create-groups',
                            '--disable-embed-rasters',
                            '--enable-comment-stripping',
                            '--enable-id-stripping',
                            '--enable-viewboxing',
                            '--indent=none',
                            '--quiet',
                            '--remove-descriptions',
                            '--remove-descriptive-elements',
                            '--remove-metadata',
                            '--remove-titles',
                            '--renderer-workaround',
                            '--shorten-ids',
                            '--strip-xml-prolog',
                        ])
                    )

                    with open(self.fp, 'w') as f:
                        f.write(out_svg.toxml())
                if self.exten == 'pdf':
                    out = '{}/orders/tmp/strip/{}-out.pdf'.format(
                        self.wd,
                        self.hash
                    )
                    self.execute(
                        '{} -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen -dNOPAUSE -dQUIET '
                        '-dBATCH -sOutputFile={} {}'.format(self.gs, out, self.fp))
                    self.fp = out
                if self.exten == 'doc' or self.exten == 'docx' or self.exten == 'pdf':
                    self.execute('{} -all:all= -Adobe:All= -overwrite_original {}'.format(self.exiftool, self.fp))
                if self.exten == 'gif' or self.exten == 'mov' or self.exten == 'mp4' or self.exten == 'webm':
                    # If WEBM or GIF convert to MP4
                    if self.exten == 'webm':
                        out = '{}/orders/tmp/strip/{}-out.mp4'.format(
                            self.wd,
                            self.hash
                        )
                        self.execute('{} -y -fflags +genpts -i {} -r 24 {}'.format(self.ffmpeg, self.fp, out))

                        self.fp = out
                        out = '{}/orders/tmp/strip/{}-out.mp4'.format(
                            self.wd,
                            self.hash
                        )
                    elif self.exten == 'gif':
                        out = '{}/orders/tmp/strip/{}-out.mp4'.format(
                            self.wd,
                            self.hash
                        )
                        self.execute(
                            '{} -y -i {} -movflags faststart -pix_fmt yuv420p -vf "scale=trunc(iw/2)*2:trunc('
                            'ih/2)*2" {}'.format(self.ffmpeg, self.fp, out))

                        self.fp = out
                        out = '{}/orders/tmp/strip/{}-out.mp4'.format(
                            self.wd,
                            self.hash
                        )
                    else:
                        out = '{}/orders/tmp/strip/{}-out.{}'.format(
                            self.wd,
                            self.hash,
                            self.exten
                        )

                    self.execute('{} -y -i {} -vf format=yuv420p -vcodec libx264 -crf 28 -preset faster '
                                 '-profile:v baseline -map_metadata -1 -c:a copy -fflags +bitexact -flags:v +bitexact '
                                 '-flags:a +bitexact {}'.format(self.ffmpeg, self.fp, out))

                    self.fp = out

                    # Convert again to WEBM from MP4 if the file was WEBM
                    # Not needed for GIF extension since a GIF is seen as an audioless-video by Telegram
                    if self.exten == 'webm':
                        out = '{}/orders/tmp/strip/{}-out.webm'.format(
                            self.wd,
                            self.hash
                        )
                        self.execute('{} -y -i {} -vcodec libvpx -cpu-used -5 -deadline realtime -map_metadata -1 '
                                     '-fflags +bitexact -flags:v +bitexact -flags:a +bitexact {}'.format(self.ffmpeg, self.fp, out))
                        self.fp = out

                self.execute('{} -all:all= -Adobe:All= -overwrite_original {}'.format(self.exiftool, self.fp))
                self.result['send'] = self.fp

                cmd = 'ls -l {}'.format(self.fp)
                res_size = run(cmd.split(), capture_output=True, text=True).stdout
                res_size = res_size.split(' ')[4]
                self.result['caption'] += '\n\nOriginale: {} Byte'.format(self.file_size)
                self.result['caption'] += '\nAttuale: {} Byte'.format(res_size)
                reduction = round(100 - (100 * int(res_size) / int(self.file_size)), 3) * -1
                self.result['caption'] += '\nBilancio: {}%'.format(reduction)
            except Exception as e:
                self.result['type'] = 'text'
                self.result['send'] = 'Qualcosa è andato storto'
                self.result['status'] = False
                self.result['err'] = str(e)
                return self.result
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Errore di connessione'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
