"""Iowa scraper
"""
import asyncio
import json
import logging
import os
import re
import shutil
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

PATH_MSEDGEDRIVER = shutil.which("msedgedriver")


class MassachusettsScraper(BaseScraper):
    def __init__(self):
        """Instantiates top-level url to begin scraping from"""
        self.election_offices_url = (
            "https://www.sec.state.ma.us/ele/eleev/ev-find-my-election-office.htm"
        )
        self.city_town_directory_url = (
            "https://www.sec.state.ma.us/ele/eleclk/clkidx.htm"
        )
        self.election_offices = []
        self.edge_options = EdgeOptions()
        self.edge_options.use_chromium = True
        self.edge_options.add_argument("--headless")
        self.driver = Edge(executable_path=PATH_MSEDGEDRIVER, options=self.edge_options)
        self.phone_jurisdiction_map = self.create_juridiction_phone_mapping()

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
            LOG.info(f"Fetching elections offices at {self.election_offices_url}...")
            self.driver.get(self.election_offices_url)
            # Convert the response into an easily parsable object
            election_offices_soup = BeautifulSoup(
                self.driver.page_source, "html.parser"
            )

            self.driver.quit()

            election_offices_div = election_offices_soup.find("div", id="content_third")
            elm: Tag
            election_office = {}
            starting_point_found = False
            office_list = election_offices_div.find_all(["h2", "p"])
            for idx, elm in enumerate(office_list):
                if not starting_point_found:
                    if elm.name == "h2":
                        starting_point_found = True
                    else:
                        continue
                if elm.name == "h2":
                    if election_office:
                        election_office["phone"] = self.phone_jurisdiction_map[
                            election_office["cityName"]
                        ]
                        election_office["website"] = self.election_offices_url
                        self.election_offices.append(election_office)
                    election_office = {
                        "cityName": " ".join(elm.getText().split())
                        .replace("\n", "")
                        .title()
                    }
                elif elm.name == "p":
                    mapping = electionsaver.addressSchemaMapping
                    text = elm.getText().strip()
                    if re.match("MAILING ADDRESS", text):
                        outliers = ["Boston", "Gardner", "Haverhill", "Princeton"]
                        city_name = election_office["cityName"]
                        parsed_address = text.split(sep="\n", maxsplit=2)[2].replace(
                            "\n", " "
                        )
                        mailing_address = usaddress.tag(
                            parsed_address, tag_mapping=mapping
                        )[0]
                        mailing_address["locationName"] = f"{city_name} Election Office"
                        election_office["mailingAddress"] = mailing_address

                        if city_name in outliers:
                            city_state_zip = usaddress.tag(
                                office_list[idx + 1].getText(), tag_mapping=mapping
                            )[0]
                            election_office["mailingAddress"].update(city_state_zip)
                    elif re.match("EMAIL", text):
                        election_office["email"] = text.split(":")[1].lstrip()
                    elif re.match("OFFICE ADDRESS", text):
                        mailing_address = election_office["mailingAddress"]
                        state = mailing_address["state"]
                        zip_code = mailing_address["zipCode"]
                        apt_number = mailing_address.get("aptNumber", "")
                        street_city = text.split(" ", maxsplit=2)[2]
                        street_city_split = street_city.split(",")
                        street = street_city_split[0]
                        if len(street_city_split) == 2:
                            city_part = f", {street_city_split[1].lstrip()},"
                        else:
                            city_part = ""
                        parsed_address = (
                            f"{street} {apt_number}{city_part} {state} {zip_code}"
                        )
                        try:
                            physical_address = usaddress.tag(
                                parsed_address, tag_mapping=mapping
                            )[0]
                        except Exception:
                            parsed_address = (
                                f'{text.split(" ", maxsplit=2)[2]}, {state} {zip_code}'
                            )
                            physical_address = usaddress.tag(
                                parsed_address, tag_mapping=mapping
                            )[0]
                        physical_address[
                            "locationName"
                        ] = f'{election_office["cityName"]} Election Office'
                        if election_office["cityName"] == "Royalston":
                            physical_address["streetNumberName"] = "10 The Common"
                        election_office["physicalAddress"] = physical_address

            with open(
                os.path.join(
                    ROOT_DIR, "scrapers", "massachusetts", "massachusetts.json"
                ),
                "w",
            ) as f:
                json.dump(self.election_offices, f)
        except Exception as e:
            LOG.exception(f"Exception: {e}")

        return self.election_offices

    def create_juridiction_phone_mapping(self):
        """
        The election office url for MA doesn't include the office's phone number.
        Instead, the website tells you to look in their town/city directory, which is
        in a separate url (nice one, MA. appreciate it). As such, this method extracts
        those phone numbers and maps them to the jurisdiction they represent for easy
        lookup when constructing the final election office objects.
        @return: mapping of town/city name to phone number
        """
        mapping = {}
        self.driver.get(self.city_town_directory_url)
        soup = BeautifulSoup(self.driver.page_source, "html.parser")

        directory = soup.find("div", id="content_third").find_all("p")
        entry: Tag
        for entry in directory:
            m = re.findall(
                r"([A-Z -]+(?=</span>))|((?<=Phone: )\d{3}-\d{3}-\d{4})",
                entry.decode_contents(),
            )
            if m:
                juridiction_name = m[0][0]
                juridiction_phone = m[1][1]
                if juridiction_name == "PEPPEREL":
                    juridiction_name += "L"
                mapping[juridiction_name.title()] = juridiction_phone
        return mapping


async def get_election_offices() -> List[Dict]:
    massachusetts_scraper = MassachusettsScraper()
    election_offices = massachusetts_scraper.scrape()

    return election_offices


if __name__ == "__main__":
    asyncio.run(get_election_offices())
