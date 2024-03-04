from secret import Secret


class ManageUser:
    def __init__(self, msg, wd, superadmin):
        self.msg = msg
        self.wd = wd
        self.superadmin = superadmin
        self.args = msg.text.split(' ')

        try:
            self.user = self.msg.reply_to_message.from_user.id
            self.is_bot = self.msg.reply_to_message.from_user.is_bot
        except Exception:
            self.user = None
            self.is_bot = None

        self.result = {
            'type': 'text',
            'send': 'Wrong command, type <code>manuser add</code> or <code>manuser rm</code> as a reply to '
                    'a user message',
            'caption': None,
            'filename': None,
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Manager permissions
    def get(self) -> dict:
        # The user is not a superadmin
        if self.superadmin is False:
            self.result['send'] = 'You don\'t have the power to use this command'
            return self.result

        # The command must have at least one argument
        if len(self.args) != 2:
            return self.result

        # The command must refer to a message
        if self.user is None or self.is_bot is None:
            return self.result

        # The command is invalid for bots
        if self.is_bot is True:
            return self.result

        # Take the arguments
        arg = str(self.args[1])
        secret = Secret(self.wd)

        if arg == 'add':
            self.result['send'] = secret.add_to_key('admin', self.user)
            return self.result

        if arg == 'rm':
            self.result['send'] = secret.rm_from_key('admin', self.user)
            return self.result

        # Else
        return self.result
