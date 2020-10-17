"""Iowa scraper
"""
import asyncio
import json
import logging
import os
import unicodedata
from typing import Dict, List

import usaddress
from bs4 import BeautifulSoup, Tag
from msedge.selenium_tools import Edge, EdgeOptions

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
from lib.scrapers.base_scraper import BaseScraper

# create logger

LOG = logging.getLogger("massachusetts_scraper")
LOG.setLevel(logging.DEBUG)

# create console handler and set level to debug.
# logging.StreamHandler(sys.stdout) to print to stdout instead of the default stderr
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
LOG.addHandler(ch)

webdriver_path = r"C:\Users\omarc\Downloads\edgedriver_win64\msedgedriver.exe"


class MassachusettsScraper(BaseScraper):
    def __init__(self):
        """Instantiates top-level url to begin scraping from"""
        self.root_url = (
            "https://www.sec.state.ma.us/ele/eleev/ev-find-my-election-office.htm"
        )
        self.data = []
        self.edge_options = EdgeOptions()
        self.edge_options.use_chromium = True
        self.edge_options.add_argument("--headless")
        self.driver = Edge(executable_path=webdriver_path, options=self.edge_options)

    def scrape(self) -> List[Dict]:
        """TODO: Write documentation once purpose of method is further defined.

        This code will only work on Windows as it stands now.
        """

        # Using selenium webdriver over requests due to needing a more sophisticated
        # way to bypass captcha for gov websites that use it. Only works on Windows
        # for now and there are some simple pre-reqs needed before it can work.
        # More info: https://selenium-python.readthedocs.io/index.html
        try:
            LOG.info("Starting webdriver...")
            # Execute GET request
            LOG.info(f"Fetching {self.root_url}...")
            self.driver.get(self.root_url)
            # Convert the response into an easily parsable object
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            # Close browser driver
            self.driver.close()

            div = soup.find("div", id="content_third")
            elm: Tag
            election_offices = []
            for elm in div.find_all(["h2", "p"]):
                election_office = {}
                starting_point_found = False
                if not starting_point_found:
                    if elm.name == "h2":
                        starting_point_found = True
                    else:
                        continue
                if elm.name == "h2":
                    election_office["cityName"] = f"{elm.text.title()} City Election Office"
                    continue




            with open(
                os.path.join(ROOT_DIR, "scrapers", "massachusetts", "massachusetts.json"), "w"
            ) as f:
                json.dump(self.data, f)
        except Exception as e:
            LOG.error(f"Exception: {e}")

        return self.data


async def get_election_offices() -> List[Dict]:
    massachusetts_scraper = MassachusettsScraper()
    election_offices = massachusetts_scraper.scrape()

    return election_offices


if __name__ == "__main__":
    asyncio.run(get_election_offices())
