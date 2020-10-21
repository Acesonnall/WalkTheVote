""" Utility functions
"""
import os
import shutil
from dataclasses import dataclass
from typing import Union

from selenium import webdriver
from selenium.webdriver import chrome, firefox

from lib.errors.wtv_errors import WalkTheVoteError


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
    name: str
    driver_options: Union[
        chrome.options.Options,
        firefox.options.Options,
    ]
    driver: Union[
        chrome.webdriver.WebDriver,
        firefox.webdriver.WebDriver,
    ]
    install_info: str
    driver_path: str = ""


class WTVWebDriver:
    def __init__(self, state):
        self._drivers = [
            _Driver(
                name="chromedriver",
                driver_options=chrome.options.Options(),
                driver=webdriver.Chrome,
                install_info="https://sites.google.com/a/chromium.org/chromedriver"
                             "/downloads",
            ),
            _Driver(
                name="geckodriver",
                driver_options=firefox.options.Options(),
                driver=webdriver.Firefox,
                install_info="https://github.com/mozilla/geckodriver/releases",
            ),
        ]

        for driver in self._drivers:
            driver.driver_path = shutil.which(driver.name)
            if driver.driver_path:
                driver.driver_options.add_argument("--headless")
                self._primary_driver = driver.driver(
                    executable_path=driver.driver_path, options=driver.driver_options
                )
                break
        else:
            raise WalkTheVoteError(self._print_error(state=state))

    def get_webdriver(self):
        return self._primary_driver

    def _print_error(self, state="State") -> str:
        error_msg = (
            f"{state} scraper requires selenium webdriver to run.\nPlease "
            f"use the webdriver for the browser of your choice and add the "
            f"path to them to your system PATH.\nSupported drivers:"
        )
        for driver in self._drivers:
            error_msg += f"\n\t{driver.name}:\n\t\tInstall info: {driver.install_info}"

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
