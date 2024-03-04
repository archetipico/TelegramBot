from subprocess import run


class Solve:
    def __init__(self, msg, executable):
        self.msg = msg
        self.executable = executable
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

    # Capture edges inside picture
    def get(self) -> dict:
        if len(self.args) == 1:
            self.result['send'] = 'Type <code>solve expression</code>\nhttps://qalculate.github.io/manual/'
            self.result['status'] = False
            return self.result

        try:
            self.result['send'] = run([self.executable, self.args[1]], capture_output=True, text=True).stdout
        except Exception as e:
            self.result['send'] = ('Error, are you sure you typed it correctly?\nhttps://qalculate.github.io/manual')
            self.result['status'] = False
            self.result['err'] = str(e)

        return self.result
