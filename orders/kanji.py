import json
from random import choice


class Kanji:
    def __init__(self, msg, wd, kanji_list):
        self.msg = msg
        self.kanji_list = kanji_list
        self.wd = wd

        self.result = {
            'type': 'document',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Get a kanji
    def get(self) -> dict:
        # Randomly select one character
        kanji_char = choice(self.kanji_list)

        # Extract values into variables
        character = kanji_char["character"]
        readings = kanji_char["readings"]
        meanings = kanji_char["meanings"]
        examples = kanji_char["examples"]
        details = kanji_char["details"]

        # Load the correct GIF
        try:
            self.result['send'] = self.wd + '/orders/utility/kanji-gifs/' + character.strip() + '.gif'
        except Exception as e:
            self.result['send'] = self.wd + '/orders/utility/kanji-gifs/no-animation.png'

        # Create a text string to save the information
        res = (
            f"<b>{character}</b>\n\n"
            f"<b>Kun</b>: {', '.join([f'{kun[0]} ({kun[1]})' for kun in readings['kun']])}\n"
            f"<b>On</b>: {', '.join([f'{on[0]} ({on[1]})' for on in readings['on']])}\n"
            f"<b>Meanings</b>: {', '.join(meanings)}\n"
        )

        for key, value in details.items():
            formatted = key.upper() if key == "jlpt" else key.capitalize()
            res += f"<b>{formatted}</b>: {value}\n"

        res += "\n<b>Examples</b>\n"
        for example in examples:
            res += (
                f"<code>{example[0]}</code>\n"
                f"  <b>Reading</b>: {', '.join(example[1])}\n"
                f"  <b>Rōmaji</b>: {', '.join(example[2])}\n"
                f"  <b>Meaning</b>: {', '.join(example[3])}\n"
            )

        self.result['caption'] = res
        return self.result
