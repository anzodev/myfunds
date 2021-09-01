from argparse import ArgumentParser
from argparse import Namespace


def env_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--env", type=str, default=None, help="environment configuration file path"
    )
    return parser


def parse_env_parser() -> Namespace:
    parser = env_parser()
    return parser.parse_args()
