import os
import sys

# Ensure the project root is on the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from lib.ElectionSaver.electionsaver import decode_email


def test_decode_email():
    encoded = "0d65686161624d68756c607d6168236e6260"
    assert decode_email(encoded) == "hello@example.com"

