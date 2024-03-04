from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from pytz import timezone, utc
from re import search
from requests import get as req
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from time import sleep


class Weather:
    def __init__(self, msg, owm, forecast=0):
        self.msg = msg
        self.owm = owm
        self.forecast = forecast

        try:
            self.search = msg.text.split(' ', 1)[1].lower()
        except Exception as e:
            self.search = None
            print(str(e))

        self.send = ''
        self.within_limits = True

        # Last two are used by InlineKeyboard
        self.result = {
            'type': 'photo',
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

    # Alarm formatting
    @staticmethod
    def format_alarm(alarm) -> str:
        res = '\n\n<b>\U000026A0 '
        res += '{} warning'.format(alarm)
        res += ' \U000026A0</b>\n'
        return res

    # Left and right formatting
    @staticmethod
    def format_all(left, right) -> str:
        # Find the longest word on the left and format based on this
        longest = len(left[0])
        res = ''
        for i in left[1:]:
            l = len(i)
            if l > longest:
                longest = l

        for i, j in zip(left, right):
            spaces = longest - len(i) + 1
            res += '{}'.format(i)
            res += spaces * ' '
            res += '{}\n'.format(j)

        return res

    # Wind and gust formatting
    @staticmethod
    def format_wind(speed, deg) -> str:
        directions = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖', '↑']
        direction = round((deg % 360) / 45)
        return '{}{}km/h'.format(directions[direction], round(speed, 1))

    # Seasons
    @staticmethod
    def get_season(lat) -> str:
        lat = float(lat)
        time_tuple = datetime.now().timetuple()
        winter_solstice = 355
        spring_equinox = 80
        summer_solstice = 172
        autumn_equinox = 266

        # Leap year
        year = time_tuple.tm_year
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
            winter_solstice += 1
            spring_equinox += 1
            summer_solstice += 1
            autumn_equinox += 1

        yday = time_tuple.tm_yday
        if winter_solstice <= yday < spring_equinox:
            return 'winter' if lat >= 0 else 'summer'
        if spring_equinox <= yday < summer_solstice:
            return 'spring' if lat >= 0 else 'autumn'
        if summer_solstice <= yday < autumn_equinox:
            return 'summer' if lat >= 0 else 'winter'
        if autumn_equinox <= yday < winter_solstice:
            return 'autumn' if lat >= 0 else 'spring'

        return 'unknown'

    # EU pollution directives https://www.eea.europa.eu/themes/air/air-quality-concentrations/AirQlimitvalues.png
    # (it's better to use WHO directives since they're lower bounds)
    # PM2.5 yearly mean level
    # PM10 yearly mean level
    # O3 seasonal mean level
    # NO2 yearly mean level
    # SO2 24h mean level
    # CO 24h mean level
    # NO 8h mean level
    # NH3 always STRICT level -> for NH3 I have 25ppm (source: https://www.engineeringtoolbox.com/ammonia-health-symptoms-d_901.html) so around ~18.000 micrograms/m^3
    def get_quality(self, soglia, val) -> None:
        if soglia == -1:
            return

        if float(val) <= float(soglia):
            return

        times = round(val / soglia, 2)
        if times <= 1.0:
            return

        self.send += '\n^ (× {})'.format(times)
        self.within_limits = False

        return

    # Return current weather
    def get(self) -> dict:
        if self.search is None:
            self.result['type'] = 'text'
            self.result['send'] = 'Digita <code>wtr [luogo]</code>'
            self.result['status'] = False
            return self.result

        try:
            # Rule 1 -> https://operations.osmfoundation.org/policies/nominatim/
            sleep(1.1)

            geolocator = Nominatim(user_agent="personal_geo_service")
            if search(r'\(\d+.?\d+?, ?\d+.?\d+?\)', self.search):
                location = geolocator.reverse(self.search[1:-1])
            else:
                location = geolocator.geocode(self.search)

            # If it fails it's because it fails to recognize coordinates, so I have to locate by myself
            try:
                lat = str(location.latitude)
                lon = str(location.longitude)
                display_name = location.address
                location_type = location.raw.get('type')
                importance = location.raw.get('importance')
            except Exception as e:
                latlon = self.search[1:-1].split(',')
                lat = str(latlon[0].strip())
                lon = str(latlon[1].strip())
                display_name = 'Coordinates'
                location_type = 'Unknown'
                importance = 'Geographical marker'

            if importance is None:
                importance = 'Reference point'

            condition = {
                'thunderstorm with light rain': '\U000026C8 Thunderstorm with light rain',
                'thunderstorm with rain': '\U000026C8 Thunderstorm with rain',
                'thunderstorm with heavy rain': '\U000026C8 Thunderstorm with heavy rain',
                'light thunderstorm': '\U0001F329 Light thunderstorm',
                'thunderstorm': '\U0001F329 Thunderstorm',
                'heavy thunderstorm': '\U0001F329 Heavy thunderstorm',
                'ragged thunderstorm': '\U0001F329 Ragged thunderstorm',
                'thunderstorm with light drizzle': '\U000026C8 Thunderstorm with light drizzle',
                'thunderstorm with drizzle': '\U000026C8 Thunderstorm with drizzle',
                'thunderstorm with heavy drizzle': '\U000026C8 Thunderstorm with heavy drizzle',
                'light intensity drizzle': '\U0001F327 Light intensity drizzle',
                'drizzle': '\U0001F327 Drizzle',
                'heavy intensity drizzle': '\U0001F327 Heavy intensity drizzle',
                'light intensity drizzle rain': '\U0001F327 Light intensity drizzle rain',
                'drizzle rain': '\U0001F327 Drizzle rain',
                'heavy intensity drizzle rain': '\U0001F327 Heavy intensity drizzle rain',
                'shower rain and drizzle': '\U0001F327 Shower rain and drizzle',
                'heavy shower rain and drizzle': '\U0001F327 Heavy shower rain and drizzle',
                'shower drizzle': '\U0001F327 Shower drizzle',
                'light rain': '\U0001F327 Light rain',
                'moderate rain': '\U0001F327 Moderate rain',
                'heavy intensity rain': '\U0001F327 Heavy intensity rain',
                'very heavy rain': '\U0001F327 Very heavy rain',
                'extreme rain': '\U0001F327 Extreme rain',
                'freezing rain': '\U00002744 Freezing rain',
                'light intensity shower rain': '\U0001F327 Light intensity shower rain',
                'shower rain': '\U0001F327 Shower rain',
                'heavy intensity shower rain': '\U0001F327 Heavy intensity shower rain',
                'ragged shower rain': '\U0001F327 Ragged shower rain',
                'light snow': '\U0001F328 Light snow',
                'snow': '\U0001F328 Snow',
                'heavy snow': '\U0001F328 Heavy snow',
                'sleet': '\U0001F328 Sleet',
                'light shower sleet': '\U0001F328 Light shower sleet',
                'shower sleet': '\U0001F328 Shower sleet',
                'light rain and snow': '\U0001F328 Light rain and snow',
                'rain and snow': '\U0001F328 Rain and snow',
                'light shower snow': '\U0001F328 Light shower snow',
                'shower snow': '\U0001F328 Shower snow',
                'heavy shower snow': '\U0001F328 Heavy shower snow',
                'mist': '\U0001F32B Mist',
                'smoke': '\U0001F32B Smoke',
                'haze': '\U0001F32B Haze',
                'sand/dust whirls': '\U0001F300 Sand/dust whirls',
                'fog': '\U0001F32B Fog',
                'sand': '\U0001F32C Sand',
                'dust': '\U0001F32C Dust',
                'volcanic ash': '\U0001F30B Volcanic ash',
                'squalls': '\U0001F32C Squalls',
                'tornado': '\U0001F32A Tornado',
                'clear sky': '\U00002600 Clear sky',
                'few clouds': '\U0001F324 Few clouds',
                'scattered clouds': '\U000026C5 Scattered clouds',
                'broken clouds': '\U0001F325 Broken clouds',
                'overcast clouds': '\U00002601 Overcast clouds'
            }

            # Take from OWM
            get = req(
                'https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&units=metric&appid={}'.format(lat, lon, self.owm),
                timeout=5
            )
            data_owm = get.json()

            # Fetch introduction
            if self.forecast != 0:
                idx = int(self.forecast / 3)
                weather = data_owm['list'][idx].get('weather')[0]
            else:
                weather = data_owm['list'][0].get('weather')[0]

            descr = condition.get(weather.get('description'), 'Condizione meteo ignota')

            # Fetch data from OpenMeteo
            url = (
                'https://api.open-meteo.com/v1/forecast?latitude={}&longitude={'
                '}&timezone=auto&hourly=temperature_2m,apparent_temperature,soil_temperature_0cm,uv_index,'
                'windspeed_10m,winddirection_10m,windgusts_10m,precipitation_probability,rain,showers,snowfall,'
                'cape,relativehumidity_2m,pressure_msl,visibility&forecast_days=2&timeformat=unixtime'
            ).format(
                lat, lon
            )
            get = req(url, timeout=5)
            data_om = get.json()
            hourly = data_om.get('hourly')
            times_om = hourly.get('time')
            # We must observe the data at the real time not at our time
            time_zone = timezone(data_om.get('timezone'))
            # Let's see time_real so we understand what time is it
            time_real = datetime.now(time_zone).replace(
                minute=0,
                second=0,
                microsecond=0
            ).astimezone(utc).timestamp()
            display_date = datetime.now(time_zone).strftime('%H:%M %d/%m/%Y')
            if self.forecast != 0:
                time_real += (3600 * self.forecast)
                display_date = (datetime.now(time_zone) + timedelta(hours=self.forecast)).replace(
                    minute=0,
                    second=0,
                    microsecond=0
                ).strftime('%H:%M %d/%m/%Y')
            hour_real = times_om.index(time_real)

            # Actual temperature
            actual_temp = '{}°C'.format(hourly.get('temperature_2m')[hour_real])
            # Apparent temperature
            feels_temp_val = hourly.get('apparent_temperature')[hour_real]
            feels_temp = '{}°C'.format(feels_temp_val)
            # Soil temperature
            soil_temp_val = hourly.get('soil_temperature_0cm')[hour_real]
            soil_temp = '{}°C'.format(soil_temp_val)

            # UV index
            uv_index_val = hourly.get('uv_index')[hour_real]
            uv_index = '{}/12'.format(uv_index_val)

            # Wind
            wind_speed = hourly.get('windspeed_10m')[hour_real]
            wind_deg = hourly.get('winddirection_10m')[hour_real]
            wind = self.format_wind(wind_speed, wind_deg)

            # Gusts
            gusts_speed = hourly.get('windgusts_10m')[hour_real]
            gusts = self.format_wind(gusts_speed, wind_deg)

            # Initial formatting
            left = ['Actual', 'Feels', 'Soil', 'UV Index', 'Wind', 'Gusts']
            right = [actual_temp, feels_temp, soil_temp, uv_index, wind, gusts]

            # Beaufort scale using m/s
            # B = 1.13 * cubic_root( v^2 )
            beaufort_sea_index = ['Calm', 'Almost calm', 'Slight movement', 'Moderate', 'Moderate', 'Very moderate',
                                    'Rough', 'Rough', 'Very rough', 'High', 'Very high', 'Very high', 'Stormy']

            beaufort_wind_index = ['Calm', 'Light air', 'Light breeze', 'Gentle breeze', 'Moderate breeze',
                                    'Fresh breeze', 'Strong breeze', 'High wind', 'Gale', 'Severe gale', 'Storm',
                                    'Violent storm', 'Hurricane']

            beaufort_wind_descr = ['None', 'None', 'None', 'None', 'None', 'None',
                                    'Raised dust and possible damage to shrubs',
                                    'Possible damage to vegetation and difficulty walking',
                                    'Damage to vegetation and inability to walk against the wind',
                                    'Possible damage to structures',
                                    'Uprooting of trees and considerable damage to structures',
                                    'Extensive damage to structures',
                                    'Severe and widespread damage to structures'
                                ]

            beaufort = min(12, int(1.13 * (((gusts_speed / 3.6) ** 2) ** (1. / 3.))))

            if isinstance(importance, str):
                self.send = '{}\n\n<i>{}</i>\n({}, {})\nRelevance: {}\n\n{}\n\U0001F343 {}\n'.format(
                    display_date,
                    display_name,
                    lat,
                    lon,
                    importance,
                    descr,
                    beaufort_wind_index[beaufort]
                )
            else:
                self.send = '{}\n\n<i>{}</i>\n({}, {})\nRelevance: {}\n\n{}\n\U0001F343 {}\n'.format(
                    display_date,
                    display_name,
                    lat,
                    lon,
                    round(importance, 2),
                    descr,
                    beaufort_wind_index[beaufort]
                )

            # Is it a sea location?
            location_type = str(location_type)
            # Leisures, naturals and places
            water_locations = [
                'bathing_place', 'beach_resort', 'fishing', 'marina', 'slipway', 'swimming_area',
                'bay', 'beach', 'blowhole', 'cape', 'coastline', 'isthmus', 'peninsula', 'reef', 'shingle', 'shoal',
                'strait', 'water',
                'archipelago', 'island', 'islet', 'sea', 'ocean'
            ]

            if location_type in water_locations:
                self.send += '\U0001F30A {}\n'.format(beaufort_sea_index[beaufort])

            self.send += '\n<code>'

            # Precipitation probability
            precip_val = hourly.get('precipitation_probability')[hour_real]
            precip = '{}%'.format(precip_val)
            left.append('Rain %')
            right.append(precip)

            # Check for rain
            rain_val = float(hourly.get('rain')[hour_real])
            if rain_val > 0:
                rain = '{}mm'.format(rain_val)
                left.append('Rain')
                right.append(rain)

            # Check for showers
            shower = float(hourly.get('showers')[hour_real])
            if shower > 0:
                shower = '{}mm'.format(shower)
                left.append('Showers')
                right.append(shower)

            # Check for snow
            snow = float(hourly.get('snowfall')[hour_real])
            if snow > 0:
                snow = '{}mm'.format(snow)
                left.append('Snow')
                right.append(snow)

            # CAPE
            cape = '{}J/kg'.format(hourly.get('cape')[hour_real])
            left.append('CAPE')
            right.append(cape)

            # Always append humidity, pressure and visibility
            humidity_val = hourly.get('relativehumidity_2m')[hour_real]
            humidity = '{}%'.format(humidity_val)
            left.append('Humidity')
            right.append(humidity)

            pressure_val = hourly.get('pressure_msl')[hour_real]
            pressure = '{}hPa'.format(pressure_val)
            left.append('Pressure')
            right.append(pressure)

            visibility = '{}m'.format(round(hourly.get('visibility')[hour_real]))
            left.append('Visibility')
            right.append(visibility)

            # Format text
            self.send += self.format_all(left, right).strip()
            self.send += '</code>'

            # Strong wind (beaufort > 5)
            if beaufort > 5:
                self.send += self.format_alarm('Wind')
                self.send += beaufort_wind_descr[beaufort]
            # If pressure <= 1013hPa and beaufort > 8
            if int(pressure_val) <= 1013 and beaufort > 8:
                self.send += ': tornado or cyclonic event risk'

            # ALLERGENS
            try:
                url = (
                    'https://air-quality-api.open-meteo.com/v1/air-quality?latitude={}&longitude={'
                    '}&timezone=auto&hourly=dust,alder_pollen,birch_pollen,grass_pollen,mugwort_pollen,'
                    'olive_pollen,ragweed_pollen&timeformat=unixtime'
                ).format(
                    lat, lon
                )
                get = req(url, timeout=5)
                data_om = get.json()
                hourly = data_om.get('hourly')

                dust = hourly.get('dust')[hour_real]
                alder = hourly.get('alder_pollen')[hour_real]
                birch = hourly.get('birch_pollen')[hour_real]
                grass = hourly.get('grass_pollen')[hour_real]
                mugwort = hourly.get('mugwort_pollen')[hour_real]
                olive = hourly.get('olive_pollen')[hour_real]
                ragweed = hourly.get('ragweed_pollen')[hour_real]

                if alder is None and birch is None and grass is None and mugwort is None and olive is None and ragweed is None:
                    raise Exception('Allergens not available')

                self.send += '\n\n<b>Pollen  [grani/m³]</b><code>'
                if alder is not None:
                    self.send += '\nAlder      {}'.format(alder)
                if birch is not None:
                    self.send += '\nBirch      {}'.format(birch)
                if grass is not None:
                    self.send += '\nGrass      {}'.format(grass)
                if mugwort is not None:
                    self.send += '\nMugwort    {}'.format(mugwort)
                if olive is not None:
                    self.send += '\nOlive      {}'.format(olive)
                if ragweed is not None:
                    self.send += '\nRagweed    {}'.format(ragweed)
                self.send += '</code>'
            except Exception:
                self.send += ''

            # AIR QUALITY
            try:
                air_quality = {
                    0: 'Excellent \U0001F929',
                    1: 'Good \U0001F970',
                    2: 'Fair \U0000263A',
                    3: 'Satisfactory \U0001F642',
                    4: 'Poor \U0001F641',
                    5: 'Very Poor \U0001F912',
                    6: 'Hazardous \U0001F480'
                }

                get = req(
                    'https://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={}&lon={}&appid={}'.format(
                        lat,
                        lon,
                        self.owm
                    ),
                    timeout=5
                )
                if self.forecast != 0:
                    data_owm = get.json().get('list')[self.forecast]
                else:
                    data_owm = get.json().get('list')[0]
                pols = data_owm.get('components')
                self.send += '\n\n<b>Air [μg/m³]</b><code>'

                co = pols.get('co')
                no = pols.get('no')
                notwo = pols.get('no2')
                othree = pols.get('o3')
                sotwo = pols.get('so2')
                pmtwo = pols.get('pm2_5')
                pmten = pols.get('pm10')
                nhthree = pols.get('nh3')

                self.send += '\nCO         {}'.format(co)
                self.get_quality(4 * 1100, co)
                self.send += '\nNO         {}'.format(no)
                self.get_quality(30 * 1000, no)
                self.send += '\nNO2        {}'.format(notwo)
                self.get_quality(10, notwo)
                self.send += '\nO3         {}'.format(othree)
                self.get_quality(60, othree)
                self.send += '\nSO2        {}'.format(sotwo)
                self.get_quality(40, sotwo)
                self.send += '\nPM2.5      {}'.format(pmtwo)
                self.get_quality(5, pmtwo)
                self.send += '\nPM10       {}'.format(pmten)
                self.get_quality(15, pmten)
                self.send += '\nNH3        {}'.format(nhthree)
                self.get_quality(18 * 1000, nhthree)

                if dust is not None:
                    self.send += '\nDust       {}'.format(dust)

                self.send += '\n---------------------'

                # Our data
                polluts = [sotwo, notwo, pmten, pmtwo, othree, co]
                # Values for optimal air quality -> https://openweathermap.org/api/air-pollution divided by 4
                bottom = [5, 10, 5, 2, 15, 1100]
                # Values for hazardous air quality -> https://openweathermap.org/api/air-pollution
                top = [350, 200, 200, 75, 180, 15400]

                # Read the air quality index:
                aqi = data_owm.get('main').get('aqi')
                # If at least 5 values over 6 totals are optimal, then it's optimal
                if aqi == 1 and self.within_limits is True:
                    optimal_index = 0
                    for p, b in zip(polluts, bottom):
                        if p < b:
                            optimal_index += 1

                    aqi = 0 if optimal_index >= 5 else aqi
                # If at least 2 values over 6 totals are hazardous, then it's hazardous
                elif aqi == 5:
                    horrible_index = 0
                    for p, t in zip(polluts, top):
                        if p > t:
                            horrible_index += 1

                    aqi = 6 if horrible_index >= 2 else aqi

                self.send += '\n{}</code>'.format(air_quality.get(aqi))

                # Warnings for hazardous or unhealthy pollutants (source: https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf))
                # I take from "Unhealthy" and then convert the ppm data

                # If CO > 12.5ppm
                if co > 15400:
                    self.send += self.format_alarm('CO')
                    self.send += ('Anyone should avoid excessive exertion.\nPeople with heart problems should avoid places with '
                                    'high concentrations of CO, such as busy areas.')

                # If NO > 25ppm
                if no > 33000:
                    self.send += self.format_alarm('NO')
                    self.send += 'Seek shelter immediately. Protect your eyes and respiratory passages.'

                # If NO2 > 361ppb
                if notwo > 731:
                    self.send += self.format_alarm('NO2')
                    self.send += ('Anyone should limit their outdoor physical activity. People with asthma, '
                                    'the elderly, and children should stay indoors.')

                # If O3 [8h] > 0.086ppm (8h because it's better to take the lower bound)
                if othree > 182:
                    self.send += self.format_alarm('O3')
                    self.send += 'Anyone should avoid outdoors exertion.'

                # If SO2 > 186ppb
                if sotwo > 525:
                    self.send += self.format_alarm('SO2')
                    self.send += ('Anyone should limit their outdoor physical activity. People with lung problems and children '
                                    'should stay indoors.')

                # If PM2.5 > 55µg/m^3
                if pmtwo > 55:
                    self.send += self.format_alarm('PM2.5')
                    self.send += ('Anyone should limit their outdoor physical activity. People with heart or lung problems, '
                                    'the elderly, and children should stay indoors and keep their activity level to a minimum.')

                # If PM10 > 255µg/m^3
                if pmten > 255:
                    self.send += self.format_alarm('PM10')
                    self.send += ('Anyone should limit their outdoor physical activity. People with heart or lung problems, '
                                    'the elderly, and children should stay indoors and keep their activity level to a minimum.')

                # If NH3 > 25ppm
                if nhthree > 18700:
                    self.send += self.format_alarm('NH3')
                    self.send += 'Seek shelter immediately. Protect your eyes and respiratory passages.'
            except Exception as e:
                self.send += '\n\nPollutants not available'
                print('Pollutants exception: ' + str(e))

            # HEALTH
            try:
                self.send += '\n\n<b>Health</b><code>\n'

                season = self.get_season(lat)
                levels = ['Low', 'Moderate', 'High', 'Very High', 'Extreme']
                mold = levels[0]
                asthma = levels[0]
                migraine = levels[0]
                mosquitoes = levels[0]

                # Molds
                if (int(humidity_val) >= 47 and int(soil_temp_val) <= 19) or (
                        int(humidity_val) >= 55 and int(soil_temp_val) <= 28):
                    if int(rain_val) > 0:
                        if int(humidity_val) >= 80:
                            if season == 'autumn' or season == 'winter':
                                mold = levels[4]
                            else:
                                mold = levels[3]
                        else:
                            mold = levels[2]
                    else:
                        mold = levels[1]

                # Asthma
                try:
                    if aqi >= 2:
                        asthma = levels[min(aqi, 4)]
                    elif mold != levels[0] or season == 'spring':
                        asthma = levels[1]
                except Exception:
                    asthma = 'N.D.'

                # Migraine
                if int(uv_index_val) >= 10 or int(feels_temp_val) >= 30 or int(feels_temp_val) <= 5:
                    if int(pressure_val) <= 1013:
                        if int(humidity_val) >= 80 or int(humidity_val) <= 40:
                            if int(gusts_speed) >= 50:
                                migraine = levels[4]
                            else:
                                migraine = levels[3]
                        else:
                            migraine = levels[2]
                    else:
                        migraine = levels[1]

                # Mosquitoes
                if int(feels_temp_val) >= 10 or int(rain_val) > 0 or season == 'summer':
                    if int(feels_temp_val) >= 20 or season == 'summer':
                        if int(feels_temp_val) >= 25:
                            if season == 'summer':
                                mosquitoes = levels[4]
                            else:
                                mosquitoes = levels[3]
                        else:
                            mosquitoes = levels[2]
                    else:
                        mosquitoes = levels[1]

                left = ['Mold', 'Asthma', 'Migraine', 'Mosquitoes']
                right = [mold, asthma, migraine, mosquitoes]
                self.send += self.format_all(left, right).strip()
                self.send += '</code>'

                # Create an inline keyboard (for 12h, so at > 9h I stop)
                if self.forecast <= 9:
                    kb = [[InlineKeyboardButton("Forward 3h", callback_data="next_wtr")]]
                    reply_markup = InlineKeyboardMarkup(kb)
                    self.result['reply_markup'] = reply_markup
            except Exception as e:
                self.send += ''
                print('Health exception: ' + str(e))

            self.result['type'] = 'text'
            self.result['send'] = self.send
        except Exception as e:
            self.result['type'] = 'text'
            self.result['send'] = 'Sorry but at the moment I cannot find <b>{}</b>'.format(self.search)
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
