import secrets

from myfunds.config import init_config
from myfunds.config import init_env_parser
from myfunds.core.models import Account
from myfunds.core.models import db_proxy
from myfunds.database import init_database
from myfunds.modules.security import PBKDF2_PasswordHasher


def main():
    parser = init_env_parser()
    args = parser.parse_args()

    config = init_config(args.env)

    db = init_database(config.DATABASE_PATH)
    db_proxy.initialize(db)

    if Account.select().where(Account.username == config.SUPERUSER).exists():
        raise RuntimeError("Superuser exists already.")

    username = config.SUPERUSER
    password = secrets.token_urlsafe(16)
    password_hasher = PBKDF2_PasswordHasher(
        hash_func=config.PBKDF2_PWD_HASHER_HASH_FUNC,
        iterations=config.PBKDF2_PWD_HASHER_ITERATIONS,
        salt_length=config.PBKDF2_PWD_HASHER_SALT_LENGTH,
    )

    Account.create(
        username=username,
        password_hash=password_hasher.make_hash(password),
    )

    print(f"Superuser added successfully!\nUsername: {username}\nPassword: {password}")


if __name__ == "__main__":
    main()
