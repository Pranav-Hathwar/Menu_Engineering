"""Shared test configuration.

Set a strong SECRET_KEY *before* app modules import settings, since the config
layer refuses weak/placeholder secrets when DEBUG is off.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789-abcdefghijklmnop")
os.environ.setdefault("DEBUG", "false")
