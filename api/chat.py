"""Vercel entry point for POST /api/chat."""

from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "maintenance"))
from chat_server import ChatHandler


class handler(ChatHandler):
    pass
