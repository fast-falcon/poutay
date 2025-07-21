import json
import bcrypt

class User:
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash.decode()
        }

    @staticmethod
    def from_dict(data):
        return User(
            username=data["username"],
            password_hash=data["password_hash"].encode()
        )

class AuthManager:
    def __init__(self, user_file='users.json'):
        self.user_file = user_file
        self.users = {}
        self.current_user = None
        self.load_users()

    def load_users(self):
        try:
            with open(self.user_file, 'r') as f:
                raw = json.load(f)
                for u in raw:
                    user = User.from_dict(u)
                    self.users[user.username] = user
        except FileNotFoundError:
            pass

    def save_users(self):
        with open(self.user_file, 'w') as f:
            json.dump([u.to_dict() for u in self.users.values()], f, indent=2)

    def signup(self, username, password):
        if username in self.users:
            raise ValueError("Username already exists")
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        self.users[username] = User(username, hashed)
        self.save_users()

    def login(self, username, password):
        user = self.users.get(username)
        if not user:
            raise ValueError("User not found")
        if bcrypt.checkpw(password.encode(), user.password_hash):
            self.current_user = user
        else:
            raise ValueError("Invalid password")

    def is_authenticated(self):
        return self.current_user is not None
