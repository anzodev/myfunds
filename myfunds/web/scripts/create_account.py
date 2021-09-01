import re
from getpass import getpass

from myfunds.core.models import Account
from myfunds.core.models import db_proxy
from myfunds.tools.security import PBKDF2_PasswordHasher
from myfunds.web.config import init_config
from myfunds.web.database import init_database
from myfunds.web.utils import parse_env_parser


args = parse_env_parser()
config = init_config(args.env)

db = init_database(config.DATABASE_PATH)
db_proxy.initialize(db)

password_hasher = PBKDF2_PasswordHasher(
    hash_func=config.PBKDF2_PWD_HASHER_HASH_FUNC,
    iterations=config.PBKDF2_PWD_HASHER_ITERATIONS,
    salt_length=config.PBKDF2_PWD_HASHER_SALT_LENGTH,
)

username = None

while True:
    try:
        if username is None:
            username = input("Username: ")
            if not re.match(r"^[a-zA-Z0-9_]{4,100}$", username):
                username = None
                raise ValueError("Wrong username value.")
        else:
            print(f"Username: {username}")

        password = getpass("Password: ")
        if not 6 <= len(password) <= 100:
            raise ValueError("Wrong password length.")

        password_copy = getpass("Repeat password: ")
        if password != password_copy:
            raise ValueError("Passwords missmatch.")

        account = Account.create(
            username=username,
            password_hash=password_hasher.make_hash(password),
        )
        print(f"New account ({account.id}) was created.")
        break

    except KeyboardInterrupt:
        break

    except Exception as e:
        print(f"ERROR: {e}")
        print("Try again ...\n")
