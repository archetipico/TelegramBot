from io import BytesIO


class Info:
    def __init__(self, msg):
        self.msg = msg

        self.result = {
            'type': 'document',
            'send': BytesIO(msg.to_json().encode()).getvalue(),
            'caption': None,
            'filename': 'info.json',
            'msg_id': msg.message_id,
            'destroy': False,
            'privacy': False,
            'stats': True,
            'err': ''
        }

    # Retrieve information about a message
    def get(self) -> dict:
        return self.result
