from orders.canny import Canny
from orders.caption import Caption
from orders.clear import Clear
from orders.color import Color
from orders.detect import Detect
from orders.eightball import EightBall
from orders.info import Info
from orders.kanji import Kanji
from orders.malus import Malus
from orders.manageuser import ManageUser
from orders.ocr import OCR
from orders.oled import OLED
from orders.paint import Paint
from orders.palette import Palette
from orders.pixel import Pixel
from orders.relief import Relief
from orders.replace import Replace
from orders.reverse import Reverse
from orders.roll import Roll
from orders.scale import Scale
from orders.solve import Solve
from orders.stats import Stats
from orders.strip import Strip
from orders.tts import TTS
from orders.urban import Urban
from orders.weather import Weather
from orders.xkcd import Xkcd
from threading import Thread
from time import time


class Order:
    def __init__(self, msg, wd, keys, exec_paths, deep_nn, classifiers, rules, kanji_list, font_params):
        self.msg = msg
        self.user = msg.from_user
        self.order = msg.text.split(' ', 1)[0].lower()
        self.res = None

        # Other params retrieval
        self.wd = wd
        self.superadmins, self.admins, self.key, self.owm = keys
        self.exec_paths = exec_paths
        self.deep_nn = deep_nn
        self.classifiers = classifiers
        self.rules = rules
        self.kanji_list = kanji_list
        self.font_params = font_params

        # Orders saved in usage.csv
        #
        # 'help' excluded because basic command
        # 'info' excluded because command used by developers (or superadmins) only
        # 'manuser' excluded because command used by developers (or superadmins) only
        # 'stats' excluded because I don't want stats about stats
        self.orders = [
            '8ball',
            'canny',
            'clr',
            'color',
            'cpt',
            'detect',
            'kanji',
            'malus',
            'ocr',
            'oled',
            'paint',
            'palette',
            'pixel',
            'relief',
            'rgx',
            'rev',
            'roll',
            'scale',
            'solve',
            'strip',
            'tts',
            'urb',
            'wtr',
            'xkcd'
        ]

    # Clean text before saving in usage.csv
    @staticmethod
    def clean_text(text) -> str:
        text = text.replace(';', '[PV]')
        text = text.replace('\n', '[NL]')
        return text

    # Remember usage activity
    def usage(self, res) -> None:
        with open('{}/orders/utility/usage.csv'.format(self.wd), 'a') as f:
            data = '{};{};{};{};{};{}\n'.format(
                self.order,
                self.user.id,
                time(),
                res['status'],
                self.clean_text(self.msg.text),
                self.clean_text(res['err'])
            )

            f.write(data)
        return

    def get_answer(self) -> None:
        res = None

        # Determine if the user is a superadmin
        superadmin = self.user.id in self.superadmins

        # Execute commands only for admins and superadmins
        if self.user.id not in self.admins and not superadmin:
            self.res = res
            return

        # Mapping every order with its arguments
        orders_map = {
            '8ball': {
                'name': EightBall,
                'args': [self.msg]
            },
            'canny': {
                'name': Canny,
                'args': [self.msg, self.key]
            },
            'clr': {
                'name': Clear,
                'args': [self.msg, self.rules]
            },
            'color': {
                'name': Color,
                'args': [self.msg]
            },
            'cpt': {
                'name': Caption,
                'args': [self.msg, self.key, self.font_params]
            },
            'detect': {
                'name': Detect,
                'args': [self.msg, self.key, self.deep_nn, self.classifiers]
            },
            'info': {
                'name': Info,
                'args': [self.msg]
            },
            'kanji': {
                'name': Kanji,
                'args': [self.msg, self.wd, self.kanji_list]
            },
            'malus': {
                'name': Malus,
                'args': [self.msg, self.wd]
            },
            'manuser': {
                'name': ManageUser,
                'args': [self.msg, self.wd, superadmin]
            },
            'ocr': {
                'name': OCR,
                'args': [self.msg, self.key]
            },
            'oled': {
                'name': OLED,
                'args': [self.msg, self.key]
            },
            'paint': {
                'name': Paint,
                'args': [self.msg, self.wd, self.key, self.exec_paths['mogrify']]
            },
            'palette': {
                'name': Palette,
                'args': [self.msg, self.key]
            },
            'pixel': {
                'name': Pixel,
                'args': [self.msg, self.wd, self.key, self.exec_paths['mogrify']]
            },
            'relief': {
                'name': Relief,
                'args': [self.msg, self.key]
            },
            'rgx': {
                'name': Replace,
                'args': [self.msg]
            },
            'rev': {
                'name': Reverse,
                'args': [self.msg, self.wd, self.key, self.exec_paths['ffmpeg']]
            },
            'roll': {
                'name': Roll,
                'args': [self.msg]
            },
            'scale': {
                'name': Scale,
                'args': [self.msg, self.wd, self.key, self.exec_paths['mogrify']]
            },
            'solve': {
                'name': Solve,
                'args': [self.msg, self.exec_paths['qalc']]
            },
            'stats': {
                'name': Stats,
                'args': [self.msg, self.wd]
            },
            'strip': {
                'name': Strip,
                'args': [self.msg, self.wd, self.key, (
                    self.exec_paths['exiftool'],
                    self.exec_paths['ffmpeg'],
                    self.exec_paths['gs'],
                    self.exec_paths['jpegoptim'],
                    self.exec_paths['optipng'],
                )]
            },
            'tts': {
                'name': TTS,
                'args': [self.msg]
            },
            'urb': {
                'name': Urban,
                'args': [self.msg]
            },
            'wtr': {
                'name': Weather,
                'args': [self.msg, self.owm]
            },
            'xkcd': {
                'name': Xkcd,
                'args': [self.msg]
            }
        }

        # Executing the order
        if self.order in orders_map:
            res = orders_map[self.order]['name'](*orders_map[self.order]['args']).get()

        self.res = res

    # 300s is the maximum response time
    def run_order(self) -> dict:
        t = Thread(target=self.get_answer)
        t.start()
        t.join(300)

        if t.is_alive():
            self.res = {
                'type': 'text',
                'send': 'I\'m sorry, but I\'m consuming too many resources and time for this command...',
                'caption': None,
                'filename': None,
                'msg_id': self.msg.message_id,
                'status': False,
                'err': 'TIMEOUT'
            }

        # Usage statistics if necessary
        if self.order in self.orders and self.res is not None:
            self.usage(self.res)

        return self.res
