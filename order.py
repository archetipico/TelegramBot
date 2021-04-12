import cv2
import json
import numpy as np
import re
import requests
import secret
import threading
import time

from bs4 import BeautifulSoup as soup
from gtts import gTTS
from skimage import io
from PIL import Image, ImageDraw
from sympy import N
from sympy import Symbol
from sympy.solvers import solve

class Order:
    def __init__( self, msg ):
        self.msg_id = msg.message_id
        self.reply = msg.reply_to_message
        self.text = msg.text
        self.text_list = self.text.split( ' ', 1 )

        self.result = {
            'type': None,
            'send': None,
            'parse': None,
            'msg_id': None
        }

    def horoscope( self ) -> None:
        params = (
            ( 'sign', self.text_list[1].lower() ),
            ( 'day', 'today' ),
        )

        post = requests.post('https://aztro.sameerkumar.website/', params=params)
        if str( post ) == '<Response [400]>':
            self.result = {
                'type': 'text',
                'send': 'I think you mispelled your sign',
                'parse': 'HTML',
                'msg_id': self.msg_id
            }
        else:
            res = json.loads( post.text )
            send = '''
                <i>- {} -</i>
                \n{}
                \n<b>Compatibility</b>: {}\n<b>Mood</b>: {}\n<b>Color</b>: {}\n<b>Lucky Number</b>: {}\n<b>Lucky Time</b>: {}
                '''.format(
                        res.get( 'current_date' ),
                        res.get( 'description'),
                        res.get( 'compatibility' ),
                        res.get( 'mood' ),
                        res.get( 'color' ),
                        res.get( 'lucky_number' ),
                        res.get( 'lucky_time' )
                    )

            self.result = {
                'type': 'text',
                'send': send,
                'parse': 'HTML',
                'msg_id': self.msg_id
            }

    

    def get_palette( self, path: str ) -> None:
        img = io.imread( path )[:, :]

        pixels = np.float32( img.reshape( -1, 3 ) )
        criteria = ( cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1 )
        flags = cv2.KMEANS_RANDOM_CENTERS
        _, labels, palette = cv2.kmeans( pixels, 5, None, criteria, 10, flags )
        _, counts = np.unique( labels, return_counts=True )

        l = len(counts)
        data = {}
        for i in range( 0, l ):
            data[counts[i]] = palette[i]

        data = sorted( data.items() )
        w, h = ( 640, 640 )
        img = Image.new( 'RGB', ( w, h ) )
        draw = ImageDraw.Draw( img )
        y1, y2 = 0, 0

        try:
            for i in range( 0, l ):
                rgb = tuple( data[i][1] )
                shape = [( 0, y1 ), ( w, y1 + 128 )]
                draw.rectangle( shape, fill=rgb )

                y1 += 128
                y2 -= 128
        except:
            pass

        img.save( './photo/palette.png' )

    def palette( self ) -> None:
        token = secret.get_key( 'telegram' )
        path_req = 'https://api.telegram.org/bot{}/getfile?file_id={}'.format(
            token,
            self.reply.photo[1].file_id
        )

        r = requests.get( path_req )
        path = r.json()['result']['file_path']
        photo_req = 'https://api.telegram.org/file/bot{}/{}'.format(
            token,
            path
        )

        thread = threading.Thread( target=self.get_palette( photo_req ) )
        thread.start()
        thread.join()

        self.result = {
            'type': 'photo',
            'send': './photo/palette.png',
            'parse': 'HTML',
            'msg_id': self.msg_id
        }



    def replace( self ) -> None:
        try:
            ref = self.reply.text
            splitted = self.text_list[1].split( ',', 1 )

            self.result = {
                'type': 'text',
                'send': re.sub( splitted[0], splitted[1][1:], ref ),
                'parse': 'HTML',
                'msg_id': self.reply.message_id
            }
        except:
            self.result = {
                'type': 'text',
                'send': 'Try answering a message and typing <code>replace regex, string</code>',
                'parse': 'HTML',
                'msg_id': ''
            }

    def solve( self ) -> None:
        parsed = self.text_list[1].split( ',', 1 )
        expr, param = parsed[0], parsed[1].strip()
        send = ''

        if param.isdigit() and int( param ) > 0:
            send = str( N( expr, param ) ).strip( '.' )
        else:
            x = Symbol( param )
            send = str( solve( expr, x ) )
        
        self.result = {
            'type': 'text',
            'send': send,
            'parse': '',
            'msg_id': self.msg_id
        }

    def tts( self ) -> None:
        try:
            lang = self.text_list[1]
            tts = gTTS( self.reply.text, lang=lang )
        except:
            tts = gTTS( self.reply.text, lang='en' )

        thread = threading.Thread( target=tts.save( './audio/tts.mp3' ) )
        thread.start()
        thread.join()

        self.result = {
            'type': 'audio',
            'send': './audio/tts.mp3',
            'parse': '',
            'msg_id': ''
        }



    air_quality = {
        1: 'Good',
        2: 'Fair',
        3: 'Moderate',
        4: 'Poor',
        5: 'Very poor'
    }

    def kelvin_to_celsius( self, temp ) -> float:
        return round( temp - 273, 1 )

    def uxtime_to_hour( self, ux_time ) -> str:
        return time.ctime( ux_time )[11:19]

    def weather( self ) -> None:
        try:
            get = requests.get( 'http://api.openweathermap.org/data/2.5/weather?q={}&appid={}'.format(
                self.text_list[1],
                secret.get_key( 'owm' )
            ) )

            data = get.json()
            coord = data.get( 'coord' )
            weather = data.get( 'weather' )[0]
            main = data.get( 'main' )
            wind = data.get( 'wind' )
            clouds = data.get( 'clouds' )
            sys = data.get( 'sys' )

            send = '{}, {} [{}, {}]\n<i>{}</i>\n'.format(
                data.get( 'name' ),
                sys.get( 'country' ),
                coord.get( 'lat' ),
                coord.get( 'lon' ),
                weather.get( 'description' ).capitalize()
            )
            send += '\nMin/Max/Avg/Felt Temperature: <code>{} / {} / {} / {} °C</code>'.format(
                self.kelvin_to_celsius( main.get( 'temp_min' ) ),
                self.kelvin_to_celsius( main.get( 'temp_max' ) ),
                self.kelvin_to_celsius( main.get( 'temp' ) ),
                self.kelvin_to_celsius( main.get( 'feels_like' ) )
            )
            send += '\nPressure: <code>{}atm</code>'.format( main.get( 'pressure' ) / 1000 )
            send += '\nHumidity: <code>{}%</code>'.format( main.get( 'humidity' ) )
            send += '\nVisibility: <code>{}km</code>'.format( data.get( 'visibility' ) / 1000 )
            send += '\nWind Speed/Deg: <code>{}m/s / {}°</code>'.format(
                wind.get( 'speed' ),
                wind.get( 'deg' )
            )
            send += '\nClouds coverage: <code>{}%</code>'.format( clouds.get( 'all') )
            send += '\nSunrise/Sunset: <code>{} / {}</code>'.format(
                self.uxtime_to_hour( sys.get( 'sunrise' ) ),
                self.uxtime_to_hour( sys.get( 'sunset' ) )
            )

            get = requests.get( 'https://api.openweathermap.org/data/2.5/air_pollution?lat={}&lon={}&appid={}'.format(
                coord.get( 'lat' ),
                coord.get( 'lon' ),
                secret.get_key( 'owm' )
            ) )

            data = get.json().get( 'list' )[0]
            pollutants = data.get( 'components' )
            
            send += '''\n\nAir quality: <code>{}</code>
                CO: <code>{}μg/m3</code>
                NO: <code>{}μg/m3</code>
                NO2: <code>{}μg/m3</code>
                O3: <code>{}μg/m3</code>
                SO2: <code>{}μg/m3</code>
                PM2.5: <code>{}μg/m3</code>
                PM10: <code>{}μg/m3</code>
                NH3: <code>{}μg/m3</code>
                '''.format(
                        self.air_quality.get( data.get( 'main' ).get( 'aqi' ), 'Unavailable data' ),
                        pollutants.get( 'co' ),
                        pollutants.get( 'no' ),
                        pollutants.get( 'no2' ),
                        pollutants.get( 'o3' ),
                        pollutants.get( 'so2' ),
                        pollutants.get( 'pm2_5' ),
                        pollutants.get( 'pm10' ),
                        pollutants.get( 'nh3' )
                    )

            self.result = {
                'type': 'text',
                'send': send,
                'parse': 'HTML',
                'msg_id': self.msg_id
            }
        except:
            self.result = {
                'type': 'text',
                'send': 'I might not have that place in my database, or the command was mispelled',
                'parse': 'HTML',
                'msg_id': self.msg_id
            }



    def urban( self ) -> None:
        content = re.sub( ' ', '+', self.text_list[1] )
        get = requests.get( 'https://www.urbandictionary.com/define.php?term={}'.format( content ) )
        html = soup( get.content, features='lxml' )
        for br in html.findAll( 'br' ):
            br.replace_with( '\n' + br.text )

        meaning = html.find( 'div', attrs={'class': 'meaning'} ).text
        example = html.find( 'div', attrs={'class': 'example'} ).text

        self.result = {
            'type': 'text',
            'send': '{}\n\n<i>{}</i>'.format( meaning, example ),
            'parse': 'HTML',
            'msg_id': self.msg_id
        }

    def get_answer( self ) -> dict:
        cmd = self.text_list[0].lower()

        if cmd == 'horoscope':
            self.horoscope()
        elif cmd == 'palette':
            self.palette()
        elif cmd == 'replace':
            self.replace()
        elif cmd == 'solve':
            self.solve()
        elif cmd == 'tts':
            self.tts()
        elif cmd == 'urban':
            self.urban()
        elif cmd == 'weather':
            self.weather()

        return self.result