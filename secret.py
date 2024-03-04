class Secret:
    def __init__(self, wd):
        self.keys = None
        self.wd = wd
        self.update_keys()

    # Retrieve keys
    def get_key(self, key) -> str:
        return self.keys.get(key)

    # Update keys
    def update_keys(self) -> None:
        with open('{}/orders/utility/superadmins'.format(self.wd)) as f:
            superadmin = [int(line.strip()) for line in f]

        with open('{}/orders/utility/admins'.format(self.wd)) as f:
            admin = [int(line.strip()) for line in f]

        with open('{}/orders/utility/secrets'.format(self.wd)) as f:
            secrets = [line.strip() for line in f]

        self.keys = {
            'superadmin': superadmin,
            'admin': admin,
            'owm': secrets[0],
            'telegram': secrets[1]
        }

    # Set key if admin added
    def set_key(self, v) -> bool:
        # Rewrite admin file
        f = open('{}/orders/utility/admins'.format(self.wd), 'w')
        for value in v:
            f.write(str(value) + '\n')
        f.close()

        # Update keys
        self.update_keys()

        # Check if all is right
        if self.keys.get('admin') == v:
            return True
        return False

    # Check if the key is an appendable list
    def check_key(self, key) -> bool:
        if key == 'owm' or key == 'telegram':
            return False
        return True

    # Add value to key
    def add_to_key(self, key, user) -> str:
        if self.check_key(key):
            v = self.keys.get(key)

            if user in v:
                return 'User already added'

            v.append(int(user))
            v.sort()

            if self.set_key(v):
                return 'User added'
            else:
                return 'Operation failed'

        return 'The key is not a list'

    # Remove value from key
    def rm_from_key(self, key, user) -> str:
        if self.check_key(key):
            v = self.keys.get(key)

            if user not in v:
                return 'User does not exist'

            v.remove(int(user))
            v.sort()

            if self.set_key(v):
                return 'User removed'
            else:
                return 'Operation failed'

        return 'The key is not a list'
