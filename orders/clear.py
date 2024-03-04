from bs4 import BeautifulSoup as soup
from re import findall, match, sub
from urllib.parse import unquote, urlparse
from urllib.request import urlopen


class Clear:
    def __init__(self, msg, rules):
        self.msg = msg
        self.reply = msg.reply_to_message
        self.rules = rules
        self.args = msg.text.split(' ', 1)

        self.result = {
            'type': 'text',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Return cleared URL
    def get(self) -> dict:
        try:
            ref = ''
            # If the reply contains some media
            if 'caption=\'' in str(self.reply) or 'caption=\"' in str(self.reply):
                ref = self.reply.caption
            else:
                ref = self.reply.text

            # If the reply contains obscured links
            if 'url=\'' in str(self.reply):
                # For each entity found, check if it's an URL
                for entity in self.reply.entities:
                    try:
                        ref += '\n' + entity.url
                    except Exception:
                        pass

                for entity in self.reply.caption_entities:
                    try:
                        ref += '\n' + entity.url
                    except Exception:
                        pass

            # Find every URL inside text
            urls = findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ref)

            # If there were no URLs, then end
            if len(urls) < 1:
                self.result['send'] = 'Il messaggio non contiene link'
                return self.result

            send = ''
            i = 1
            # For each URL found
            for url in urls:
                # Remember the original url
                original_url = url
                # Check for special redirects in the url (e.g. outlook redirects)
                redirects = findall(r'(?:%3F)?(?<=url\=).*', url)
                if len(redirects) > 0:
                    url = redirects[0]
                # Decode any % value
                url = unquote(url)
                # Try to deAMP
                url = sub('www.google.com/amp/s/amp.', '', url)
                url = sub('www.google.com/amp/s/', '', url)
                url = sub('amp/$', '', url)
                # Try to remove the first half of the URL if it's a Google Maps photo
                tmp_url = sub(r'(http[s]?://)?www.google.com/maps.*(?=http)', '', url)
                # If the result is different from the url then we removed something
                if len(tmp_url) != len(url):
                    # Thus we remove every thing we have after the '='
                    tmp_url = sub(r'(?=\=).*', '', tmp_url)
                # Recast always
                url = tmp_url
                # It could still contain an AMP, we must retrieve it from <link rel="canonical" ...>
                if len(findall('(amp|AMP)', url)) > 0:
                    html = urlopen(url).read()
                    data = soup(html, features="html.parser")
                    link = data.find('link', rel = 'canonical')
                    url = link['href']

                # Replace fxtwitter with twitter
                url = sub('//(www\.)?fxtwitter', '//twitter', url)
                # Replace fixupx with x
                url = sub('//(www\.)?fixupx', '//x', url)
                # Replace ddinstagram with instagram
                url = sub('//(www\.)?ddinstagram', '//www.instagram', url)
                # Replace any youtube instance to youtube
                url = sub('//(www\.)?(youtube\.com|youtu\.be)', '//www.youtube.com', url)

                # For each provider
                for k, v in self.rules['providers'].items():
                    # If the provider matches the URL
                    if match(v['urlPattern'], url):
                        # Parse url
                        parsed = urlparse(url)
                        queries = parsed.query.split('&')
                        path = parsed.path
                        if len(queries) < 1 or (len(queries) == 1 and queries[0] == ''):
                            queries = parsed.path.split('&')[1:]
                            path = parsed.path.split('&')[0]
                        good_queries = []

                        # For each query
                        for query in queries:
                            good = True

                            # If the query matches a rule, mark as failed and don't add it
                            for rule in v['rules']:
                                if match(rule, query):
                                    good = False
                                    break

                            # Same as before but a query may not have this
                            try:
                                for rule in v['referralMarketing']:
                                    if match(rule, query):
                                        good = False
                                        break
                            except Exception:
                                pass

                            if good:
                                good_queries.append(query)

                            # If the query matches a rawRule, remove it (rawRules may not exist)
                            try:
                                for raw_rule in v['rawRules']:
                                    path = sub(raw_rule, '', parsed.path)
                            except Exception:
                                pass

                        # Recreate the url
                        url = (parsed.scheme + '://' + parsed.netloc + path + '?' + parsed.params + '&'.join(good_queries)
                            + parsed.fragment)

                        # Remove trailing ? if necessary
                        if url[-1] == '?':
                            url = url[:-1]

                url = url
                # Replace to better sites
                url = sub('//(www\.)?twitter', '//fxtwitter', url)
                url = sub('//(www\.)?x', '//fixupx', url)
                url = sub('//(www\.)?(youtube\.com|youtu\.be)', '//yewtu.be', url)
                url = sub('\/\/(www\.)?(reddit.com|reddit.com/domain/old.reddit.com/)', '//old.reddit.com', url)
                url = sub('//(www\.)?instagram', '//www.ddinstagram', url)
                url = sub('(.*//.*)(tiktok.com)', 'https://proxitok.pussthecat.org', url)
                # Send result
                send += '[' + str(i) + '] ' + url + '\n'

                if len(self.args) == 2:
                    if self.args[1] == '-js':
                        send += '[' + str(i) + '-12ft] https://12ft.io/' + url + '\n'

                # Divisor
                send += '\n'
                i += 1

            if send != '':
                self.result['send'] = send
        except:
            self.result['send'] = 'Answer to a message with <code>clr</code>'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
