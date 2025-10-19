import sys
from dotenv import load_dotenv
import os
import requests

load_dotenv()

APP_URL = os.getenv("API_URL", "http://127.0.0.1:5000/")

def test_basic():
    assert 4 == 4

def test_connection():
    """Simple integration test: ensure Flask backend responds at root URL."""

    r = requests.get(APP_URL, timeout=3)

    assert r.status_code == 200, f"Expected 200 from {APP_URL}, got {r.status_code}"
