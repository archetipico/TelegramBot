from random import choice


class EightBall:
    def __init__(self, msg):
        self.msg = msg

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

    # Roll the magic 8-ball
    def get(self) -> dict:
        answers = [
            '\U0001F7E9 As I see it, yes',
            '\U0001F7E9 It is certain',
            '\U0001F7E9 It is decidedly so',
            '\U0001F7E9 Most likely',
            '\U0001F7E9 Outlook good',
            '\U0001F7E9 Signs point to yes',
            '\U0001F7E9 Without a doubt',
            '\U0001F7E9 Yes',
            '\U0001F7E9 Yes – definitely',
            '\U0001F7E9 You may rely on it',
            '\U0001F7E8 Reply hazy, try again',
            '\U0001F7E8 Ask again later',
            '\U0001F7E8 Better not tell you now',
            '\U0001F7E8 Cannot predict now',
            '\U0001F7E8 Concentrate and ask again',
            '\U0001F7E5 Don\'t count on it',
            '\U0001F7E5 My reply is no',
            '\U0001F7E5 My sources say no',
            '\U0001F7E5 Outlook not so good',
            '\U0001F7E5 Very doubtful',
        ]

        try:
            self.result['send'] = choice(answers)
        except Exception as e:
            self.result['send'] = 'Something went wrong'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
