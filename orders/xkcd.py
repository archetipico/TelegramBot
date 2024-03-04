from bs4 import BeautifulSoup as soup
from requests import get as req


class Xkcd:
    def __init__(self, msg):
        self.msg = msg

        self.result = {
            'type': 'document',
            'send': '',
            'caption': 'xkcd.com',
            'filename': 'xkcd.png',
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Return xkcd joke
    def get(self) -> dict:
        try:
            get = req('https://c.xkcd.com/random/comic', stream=True)
            html = soup(get.content, 'html.parser')
            comic = html.find('div', attrs={'id': 'middleContainer'})
            data = comic.findAll('a')[-1].text

            self.result['send'] = data
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Connection error'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
