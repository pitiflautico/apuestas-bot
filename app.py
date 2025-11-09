"""Main entry point for Sports Props Intelligence Bot dashboard"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import and run dashboard
from reporting.dashboard import main

if __name__ == "__main__":
    main()
