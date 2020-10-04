""" Utility functions
"""
import os


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

TEST_DB_URI = os.environ.get("WTV_TEST_DB_URI")
TEST_DB_NAME = os.environ.get("WTV_TEST_DB_NAME")
TEST_DB_ALIAS = os.environ.get("WTV_TEST_DB_ALIAS")

PROD_DB_URI = os.environ.get("WTV_PROD_DB_URI")
PROD_DB_NAME = os.environ.get("WTV_PROD_DB_NAME")
PROD_DB_ALIAS = os.environ.get("WTV_PROD_DB_ALIAS")

LOCAL_DB_URI = os.environ.get("WTV_LOCAL_DB_URI")
LOCAL_DB_NAME = os.environ.get("WTV_LOCAL_DB_NAME")
LOCAL_DB_ALIAS = os.environ.get("WTV_LOCAL_DB_ALIAS")
