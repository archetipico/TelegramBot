from random import randint


class Roll:
    def __init__(self, msg):
        self.msg = msg
        self.args = msg.text.split(' ', 1)
        self.reply = msg.reply_to_message

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

    # Roll a dice
    def get(self) -> dict:
        try:
            n = int(self.args[1].strip()) if len(self.args) > 1 else 6
            send = randint(1, n) if n > 1 else 'It doesn\'t make much sense, don\'t you think?'
            self.result['send'] = send
        except Exception as e:
            self.result['send'] = 'Type <code>roll[ n]</code>'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
