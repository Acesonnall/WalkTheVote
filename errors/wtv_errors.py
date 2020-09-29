"""Walk The Vote error handling
"""


class WalkTheVoteError(Exception):
    """Base class for exceptions in this module."""

    def __init__(self, message):
        self.message = message
