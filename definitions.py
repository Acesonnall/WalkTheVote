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

TEST_DB_URI = os.environ.get("MONGO_DB_TEST_URI")
TEST_DB_NAME = os.environ.get("MONGO_DB_TEST_NAME")
TEST_DB_ALIAS = os.environ.get("MONGO_DB_TEST_ALIAS")

PROD_DB_URI = os.environ.get("MONGO_DB_PROD_URI")
PROD_DB_NAME = os.environ.get("MONGO_DB_PROD_NAME")
PROD_DB_ALIAS = os.environ.get("MONGO_DB_PROD_ALIAS")

LOCAL_DB_URI = os.environ.get("MONGO_DB_LOCAL_URI")
LOCAL_DB_NAME = os.environ.get("MONGO_DB_LOCAL_NAME")
LOCAL_DB_ALIAS = os.environ.get("MONGO_DB_LOCAL_ALIAS")
