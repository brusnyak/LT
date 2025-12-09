import sys
import os
from pathlib import Path

# Add the 'backend' directory to sys.path so 'app' can be imported as a top-level package
sys.path.insert(0, str(Path(__file__).parent.parent))
