#!/usr/bin/python3
"""systemd entry point: `python3 -I run.py serve ...` (-I ignores env/user site; path set explicitly)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from lifeos_platform.__main__ import main  # noqa: E402

sys.exit(main())
