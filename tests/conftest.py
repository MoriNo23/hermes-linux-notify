import os
import sys

# Repository root is a plugin package (has __init__.py with relative imports),
# so pytest must NOT be handed it via package semantics. Insert it on sys.path
# so `import session` / `import notify` resolve as plain top-level modules.
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)