"""Iowa scraper
"""
import asyncio
import json
import logging
import os
import unicodedata
from pprint import pprint
from typing import Dict, List

import usaddress
from bs4 import BeautifulSoup
from msedge.selenium_tools import Edge, EdgeOptions

from lib.ElectionSaver import electionsaver
from lib.definitions import ROOT_DIR
from lib.scrapers.base_scraper import BaseScraper

# create logger

LOG = logging.getLogger("iowa_scraper")
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


class IowaScraper(BaseScraper):
    def __init__(self):
        """Instantiates top-level url to begin scraping from"""
        self.root_url = (
            "https://sos.iowa.gov/elections/auditors/auditor.asp?CountyID=00"
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
        exit_code = 0

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
            # Extract list of county names
            county_name_list = soup.article.find_all("img", class_="auditor", alt=True)
            # Extract tables where address and phone numbers are stored
            tables = soup.article.find_all("table")
            # Process county name and tables in parallel. Each table is uniform so we
            # can use a modulus operator too look up exact info.
            for county, table in zip(county_name_list, tables):
                # Prep helper vars
                phone, email, office_supervisor, website, location_name, county_name = (
                    "",
                ) * 6
                physical_address, mailing_address = ({},) * 2
                # Decode into format humans can read
                location_name: str
                office_supervisor, location_name = tuple(
                    (x.strip() for x in county["alt"].split(sep=","))
                )
                county_name = location_name.split(maxsplit=1)[0]
                # Extract table body
                table_body = table.find("tbody")
                # Extract table rows
                rows = table_body.find_all("tr")
                # Iterate through rows
                for idx, tr in enumerate(rows):
                    # Extract columns of rows
                    cols = tr.find_all("td")
                    # List column elements
                    cols = [
                        unicodedata.normalize("NFKD", ele.text.strip()) for ele in cols
                    ]
                    # Get phone number
                    if idx % 12 == 1:
                        phone = cols[0]
                    # Get email address
                    if idx % 12 == 3:
                        email = cols[0]
                    # Get website
                    if idx % 12 == 5:
                        website = cols[0]

                    mapping = electionsaver.addressSchemaMapping

                    address_string = " ".join(cols[0].split()) if cols else ""
                    # Get mailing address
                    if idx % 12 == 9:
                        mailing_address = usaddress.tag(
                            address_string, tag_mapping=mapping
                        )[0]
                        mailing_address["locationName"] = location_name
                    # Get physical address
                    if idx % 12 == 11:
                        physical_address = usaddress.tag(
                            address_string, tag_mapping=mapping
                        )[0]
                        physical_address["locationName"] = location_name

                        # append to data buffer
                        self.data.append(
                            {
                                "countyName": county_name,
                                "physicalAddress": physical_address,
                                "mailingAddress": mailing_address,
                                "phone": phone,
                                "email": email,
                                "officeSupervisor": office_supervisor,
                                "supervisorTitle": "County Clerk",
                                "website": website,
                            }
                        )

            with open(
                os.path.join(ROOT_DIR, "scrapers", "iowa", "iowa.json"), "w"
            ) as f:
                json.dump(self.data, f)
        except Exception as e:
            LOG.error(f"Exception: {e}")

        return self.data


async def get_election_offices() -> List[Dict]:
    iowa_scraper = IowaScraper()
    election_offices = iowa_scraper.scrape()

    return election_offices


if __name__ == "__main__":
    asyncio.run(get_election_offices())
