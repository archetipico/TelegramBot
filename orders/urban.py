from bs4 import BeautifulSoup as soup
from re import sub
from requests import get as req
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


class Urban:
    def __init__(self, msg, idx=0):
        self.msg = msg
        self.idx = idx

        try:
            self.search = msg.text.split(' ', 1)[1].lower()
        except Exception:
            self.search = None

        self.result = {
            'type': 'text',
            'send': None,
            'caption': None,
            'filename': None,
            'reply_markup': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Return urban dictionary definition
    def get(self, ) -> dict:
        if self.search is None:
            self.result['send'] = 'Type <code>urb [search]</code>'
            self.result['status'] = False
            return self.result

        try:
            content = sub(' ', '+', self.search)
            get = req('https://www.urbandictionary.com/define.php?term={}'.format(content), stream=True)
            html = soup(get.content, 'html.parser')
            for br in html.findAll('br'):
                br.replace_with('\n' + br.text)

            meaning_arr = html.findAll('div', attrs={'class': 'meaning'})
            meaning = meaning_arr[self.idx].text
            meaning = sub(r'[<>]', '', meaning)

            example_arr = html.findAll('div', attrs={'class': 'example'})
            example = example_arr[self.idx].text
            example = sub(r'[<>]', '', example)

            self.result['send'] = '{}\n\n<i>{}</i>'.format(meaning, example)
            # Create an inline keyboard
            if self.idx < len(meaning_arr) - 1:
                kb = [[InlineKeyboardButton("Next", callback_data="next_urb")]]
                reply_markup = InlineKeyboardMarkup(kb)
                self.result['reply_markup'] = reply_markup
        except Exception as e:
            self.result['send'] = ('Sorry, I can\'t find <b>{}</b>... or currently I\'m having '
                                   'connection issues').format(self.search)
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
