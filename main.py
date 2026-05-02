"""Shim so `uv run python main.py` still works."""

from ptc.cli import main

if __name__ == "__main__":
    main()
