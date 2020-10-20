""" Utility functions
"""
import os
from dataclasses import dataclass


class Bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


@dataclass
class _Driver:
    driver: str
    install_info: str


class SupportedWebDrivers:
    def __init__(self):
        self.drivers = [
            _Driver(
                "msedgedriver",
                "https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/",
            ),
            _Driver(
                "chromedriver",
                "https://sites.google.com/a/chromium.org/chromedriver/downloads",
            ),
            _Driver("geckodriver", "https://github.com/mozilla/geckodriver/releases"),
            _Driver(
                "safaridriver",
                "https://webkit.org/blog/6900/webdriver-support-in-safari-10/",
            ),
        ]

    def print_error(self, state) -> str:
        error_msg = f"{state} scraper requires selenium webdriver to run.\nPlease " \
                    f"use the webdriver for the browser of your choice and add the " \
                    f"path to them to your system PATH.\nSupported drivers: "
        for driver in self.drivers:
            error_msg += f"{driver.driver}:\n\tInstall info: {driver.install_info}\n"

        return error_msg


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
