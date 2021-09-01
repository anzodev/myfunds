from abc import ABC
from abc import abstractmethod

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


class PasswordHasher(ABC):
    @abstractmethod
    def make_hash(self, password: str) -> str:
        ...

    @abstractmethod
    def is_hash_correct(self, password_hash: str, password: str) -> bool:
        ...


class PBKDF2_PasswordHasher(PasswordHasher):
    def __init__(
        self, hash_func: str = "sha256", iterations: int = 80000, salt_length: int = 16
    ):
        self._method = f"pbkdf2:{hash_func}:{iterations}"
        self._salt_length = salt_length

    def make_hash(self, password: str) -> str:
        return generate_password_hash(password, self._method, self._salt_length)

    def is_hash_correct(self, password_hash: str, password: str) -> bool:
        return check_password_hash(password_hash, password)
