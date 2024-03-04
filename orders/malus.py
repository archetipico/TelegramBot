from random import choice, randint
from re import findall, sub


class Malus:
    def __init__(self, msg, wd):
        self.msg = msg

        try:
            self.user = self.msg.reply_to_message.from_user
        except Exception:
            self.user = self.msg.from_user

        try:
            self.subject = self.user.first_name + ' ' + self.user.last_name
        except Exception:
            self.subject = self.user.first_name

        self.path = '{}/orders/utility/mali'.format(wd)

        self.result = {
            'type': 'text',
            'send': '',
            'caption': None,
            'filename': None,
            'msg_id': None,
            'destroy': False,
            'privacy': False,
            'status': True,
            'err': ''
        }

    # Retrieve asingle malus
    @staticmethod
    def retrieve_choice(mali):
        # Pick a malus
        malus = str(choice(mali).strip())
        # Check if the malus contains a [digit:digit]
        all_matches = findall(r'\[(-?\d+):(-?\d+)\]', malus)
        # For each match... (digit, digit)
        for single_match in all_matches:
            l, r = single_match
            # Substitute just the first occurrence (as it parses, the n-th element will always be the first as the
            # previous would be already converted)
            malus = sub(r'\[(-?\d+):(-?\d+)\]', str(randint(int(l), int(r))), malus, count=1)

        return malus

    # Return malus
    def get(self) -> dict:
        done = False
        splitted = self.msg.text.split(' ', 2)

        if len(splitted) == 1:
            f = open(self.path)
            mali = f.readlines()

            self.result['send'] = '{} {}'.format(
                self.subject,
                self.retrieve_choice(mali)
            )

            f.close()
            done = True
        elif len(splitted) == 2:
            if splitted[1] == 'show':
                self.result['type'] = 'document'
                self.result['send'] = self.path
                self.result['msg_id'] = self.msg.message_id
                done = True
            else:
                f = open(self.path)
                mali = f.readlines()

                self.result['send'] = '{} {}'.format(
                    splitted[1],
                    self.retrieve_choice(mali)
                )

                f.close()
                done = True
        elif len(splitted) == 3:
            cmd = splitted[1]
            val = str(splitted[2])

            if cmd == 'add':
                f = open(self.path)
                mali = f.readlines()

                if val + '\n' in mali:
                    self.result['send'] = 'Malus <i>{}</i> already added'.format(val)
                    self.result['msg_id'] = self.msg.message_id
                else:
                    # If something like [digit1:digit2] is inserted
                    all_matches = findall(r'\[([^[\]:]+):([^[\]:]+)\]', val)
                    all_matches = [(match[0], match[1]) for match in all_matches]
                    for single_match in all_matches:
                        l, r = single_match

                        # Check if the value is int
                        if str(l)[0] == '-':
                            l = str(l)[1:]
                        if str(r)[0] == '-':
                            r = str(r)[1:]

                        if not str(l).isdigit() or not str(r).isdigit():
                            self.result['send'] = 'Invalid formatting: {} and/or {} are not of type <code>int</code>'.format(str(l), str(r))
                            self.result['msg_id'] = self.msg.message_id
                            done = True
                            break

                        # check if digit1 < digit2, otherwise return
                        if int(l) >= int(r):
                            self.result['send'] = 'Invalid formatting: {} >= {}'.format(str(l), str(r))
                            self.result['msg_id'] = self.msg.message_id
                            done = True
                            break

                    # Passed the check
                    if not done:
                        mali.append(val + '\n')
                        mali.sort()
                        out = ''.join([str(s) for s in mali])

                        f = open(self.path, 'w')
                        f.write(out)

                        self.result['send'] = 'Malus <i>{}</i> added'.format(val)
                        self.result['msg_id'] = self.msg.message_id

                f.close()
                done = True
            elif cmd == 'rm':
                f = open(self.path)
                mali = f.readlines()

                try:
                    mali.remove(val + '\n')

                    out = ''.join([str(s) for s in mali])

                    f = open(self.path, 'w')
                    f.write(out)
                    f.close()

                    self.result['send'] = 'Malus <i>{}</i> removed'.format(val)
                except Exception as e:
                    f.close()

                    self.result['send'] = 'Malus <i>{}</i> not in list'.format(val)
                    self.result['status'] = False
                    self.result['err'] = str(e)

                done = True
                self.result['msg_id'] = self.msg.message_id
            # If I type "malus john doe"
            else:
                if len(splitted[1]) + len(splitted[2]) > 100:
                    self.result['send'] = 'Too long...'.format(val)
                    self.result['msg_id'] = self.msg.message_id
                    done = True
                else:
                    f = open(self.path)
                    mali = f.readlines()

                    self.result['send'] = '{} {} {}'.format(
                        splitted[1],
                        splitted[2],
                        self.retrieve_choice(mali)
                    )

                    f.close()
                    done = True

        if not done:
            self.result['send'] = 'Wrong command, type <code>malus</code>'
            self.result['status'] = False

        return self.result
