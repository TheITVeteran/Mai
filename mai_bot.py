"""CLI entry: `python mai_bot.py` (same as `python -m mai.bot`)."""

import sys

from mai.bot import main

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: python mai_bot.py")
        print("Loads .env and runs the Mai Discord bot. No other arguments.")
        raise SystemExit(0)
    main()
