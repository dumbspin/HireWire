# conftest.py — adds the repo root to sys.path so tests can import local modules
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
