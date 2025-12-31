import secrets
import string

class SecurityManager:
    @staticmethod
    def generate_token(length=16):
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))