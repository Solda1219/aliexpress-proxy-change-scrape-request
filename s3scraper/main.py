import argparse

from db import create_session
from cli import main_cli

if __name__ == "__main__":
    session = create_session()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keyword", help="keyword/phrase to search", type=str, nargs="?", const="",
    )
    parser.add_argument(
        "--limit", help="limit search results", type=int, nargs="?", const=99999,
    )
    parser.add_argument(
        "--proxy_limit", help="limit search results", type=int, nargs="?", const=10,
    )
    parser.add_argument(
        "--cli", help="Use the CLI", dest="use_cli", action="store_true",
    )

    parser.set_defaults(use_cli=True)
    args = parser.parse_args()

    kwargs_defaults = {"limit": 99999, "proxy_limit": 10}

    kwargs = {
        k: v if v is not None else kwargs_defaults.get(k) for k, v in args._get_kwargs()
    }

    if kwargs["use_cli"]:
        main_cli(session=session)
