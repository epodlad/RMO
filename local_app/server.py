"""Compatible local entry point for the RMO application."""
import sys
from web_app.server import main

if __name__ == "__main__":
    if "--local" not in sys.argv:
        sys.argv.insert(1, "--local")
    main()
