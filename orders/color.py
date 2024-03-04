from bs4 import BeautifulSoup as soup
from requests import get as req


class Color:
    def __init__(self, msg):
        self.msg = msg

        try:
            self.search = msg.text.split(' ', 1)[1].lower()
        except Exception:
            self.search = None

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

    # Return color definition
    def get(self) -> dict:
        if self.search is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Type <code>color [hex]</code>'
            self.result['status'] = False
            return self.result

        try:
            get = req('https://www.colorhexa.com/{}'.format(self.search), stream=True)

            if get.status_code == 404:
                self.result['type'] = 'text'
                self.result['send'] = ('Sorry but <code>{}</code> is not a color.\nTry with valid colors, '
                                       'like <code>color 1155FF</code>').format(self.search)
                self.result['status'] = False
                return self.result

            html = soup(get.content, 'html.parser')

            # Exact name
            name = html.find('div', attrs={'class': 'color-description'}).find('strong').text
            self.result['caption'] = '<i>{}\n</i>'.format(name)

            # Description
            description = html.find('p', attrs={'class': 'description'}).text
            lines = description.split('. ')
            lines = [line.strip() for line in lines]

            cmyk = lines[1][31:].capitalize()
            hsl = lines[2]
            blend = lines[3]
            css = lines[4]

            # Result
            start_pos = lines[0].find('(')
            if start_pos > -1:
                end_pos = lines[0].find(')')
                known = 'A' + lines[0][start_pos + 2:end_pos]
                rgb = 'It ' + lines[0][end_pos + 3:]
                self.result['caption'] += '{}\n'.format(known)
            else:
                rgb = 'It ' + lines[0][34:]

            self.result['caption'] += '\n<b>RGB</b>\n{}\n\n'.format(rgb)
            self.result['caption'] += '<b>CMYK</b>\n{}\n\n'.format(cmyk)
            self.result['caption'] += '<b>HSL</b>\n{}\n\n'.format(hsl)
            self.result['caption'] += '<b>Blending</b>\n{}\n\n'.format(blend)
            self.result['caption'] += '<b>Websafe</b>\n{}\n\n'.format(css)
            self.result['send'] = 'https://www.colorhexa.com/{}.png'.format(self.search)
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = ('Your color does not exist or you typed something wrong, try with <code>color '
                                   '000000</code>... if nothing works, maybe I think I\'m having connection issues').format(self.search)
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
