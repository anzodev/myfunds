import getpass

from myfunds.web.tools import password_hasher


iterations = int(input("Password hasher iterations: "))
salt_length = int(input("Password hasher salt length: "))
password = getpass.getpass("Password: ")

ph = password_hasher.PBKDF2_SHA256_PasswordHasher()
password_hash = ph.make_hash(password, iterations, salt_length)

print(f"Result: {password_hash}")
