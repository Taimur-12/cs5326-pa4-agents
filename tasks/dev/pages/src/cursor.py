"""Opaque pagination cursors."""
import base64
import json


def encode_cursor(key):
    return base64.urlsafe_b64encode(json.dumps({"after": key}).encode()).decode()


def decode_cursor(cursor):
    return json.loads(base64.urlsafe_b64decode(cursor.encode()))["after"]
