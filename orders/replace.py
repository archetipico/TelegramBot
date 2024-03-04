from re import sub


class Replace:
    def __init__(self, msg):
        self.msg = msg
        self.args = msg.text.split(' ', 1)
        self.reply = msg.reply_to_message

        self.result = {
            'type': 'text',
            'send': None,
            'caption': None,
            'filename': None,
            'msg_id': msg.reply_to_message.message_id,
            'destroy': True,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Replace text
    def get(self) -> dict:
        try:
            # If the reply contains some media
            if 'caption=\'' in str(self.reply) or 'caption=\"' in str(self.reply):
                ref = self.reply.caption
            else:
                ref = self.reply.text

            splitted = self.args[1].split(',', 1)
            if splitted[1] != '':
                send = sub(splitted[0], splitted[1][1:], ref)
            else:
                send = sub(splitted[0], '', ref)

            if send == '':
                send = '<code>Void.</code>'

            self.result['send'] = send
        except Exception as e:
            self.result['send'] = 'Reply to a message with <code>rgx expression, text</code>'
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
