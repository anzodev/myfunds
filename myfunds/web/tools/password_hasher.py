from abc import ABC
from abc import abstractmethod

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


class PasswordHasher(ABC):
    @abstractmethod
    def make_hash(self, password: str) -> str:
        ...

    @abstractmethod
    def is_password_correct(self, password_hash: str, password: str) -> bool:
        ...


class PBKDF2_SHA256_PasswordHasher(PasswordHasher):
    def make_hash(self, password: str, iterations: int, salt_length: int) -> str:
        method = f"pbkdf2:sha256:{iterations}"
        return generate_password_hash(
            password=password,
            method=method,
            salt_length=salt_length,
        )

    def is_password_correct(self, password_hash: str, password: str) -> bool:
        return check_password_hash(password_hash, password)
