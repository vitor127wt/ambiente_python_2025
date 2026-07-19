#!/usr/bin/env python
import sys
from pathlib import Path

import my_package.main


def main() -> None:
    args: list[str] = sys.argv
    path: Path = Path.cwd()
    my_package.main.main(args, path)


if __name__ == "__main__":
    main()
