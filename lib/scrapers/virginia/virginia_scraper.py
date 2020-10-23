import asyncio
import json
import os
import re
import shutil
import time

from bs4 import BeautifulSoup as bS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import usaddress

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://vote.elections.virginia.gov/VoterInformation/PublicContactLookup"
PATH_CHROMEDRIVER = shutil.which("chromedriver")


def format_address_data(address_data):
    mapping = electionsaver.addressSchemaMapping

    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    final_address = {}

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]

    return final_address

async def get_election_offices():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options, executable_path=PATH_CHROMEDRIVER)
    driver.get(URL)

    dropdown = Select(driver.find_element_by_id("LocalityUid"))
    localities = [option.text for option in dropdown.options][1:]
    master_list = []

    for locality in localities:   
        dropdown = Select(driver.find_element_by_id("LocalityUid"))
        button = driver.find_element_by_class_name("saveButton")
        dropdown.select_by_visible_text(locality)
        button.click()

        # who spells label like lable??
        labels = [label.text for label in \
            driver.find_elements_by_class_name("display-lable")]
        fields = [field.text for field in \
            driver.find_elements_by_class_name("display-field")]
        data = dict(zip(labels, fields))

        # data["Facility"] contains a more specific offic name for location_name
        # in ~60% of the entries, but the other ~40% are a complete mess.
        # probably better to just list all as the election office?
        location_name = f"{locality.title()} Election Office"

        county = locality.title() if locality[-6:] != 'COUNTY' else locality[:-7].title()

        if "Address" in data:
            zip_code = data["Address"].split()[-1][:5]
            city = re.search("\n(.*), VA", data["Address"]).group(1)
            po_box = None
            address_data = data["Address"].split("\n")[0].title()

        else: # "Physical Address" and "Mailing Address" are in data!
            zip_code = data["Physical Address"].split()[-1][:5]
            city = re.search("\n(.*), VA", data["Physical Address"]).group(1)
            poss_po_string = data["Mailing Address"].split('\n')[0]
            po_box = poss_po_string if re.match("P.?O.?", poss_po_string) else None
            if county == "Prince Edward":
                address_data = "124 N. Main Street, 2nd Floor"
            elif county == "New Kent":
                address_data = "7911 Courthouse Way Ste 400"
            elif county == "Suffolk City":
                address_data = "440 Market Street"
            else:
                address_data = data["Physical Address"].split("\n")[0].title()

        subschema = format_address_data(address_data)

        schema = {
            "countyName": county,
            "physicalAddress": {
                "city": city,
                "state": "Virginia",
                "zipCode": zip_code,
                "locationName": location_name,
            },
            "phone": data["Phone"][:12],
            "email": data["Email"],
            "officeSupervisor": data["Registrar"].title(),
            "website": data["URL"] or URL,
        }

        if po_box:
            schema["physicalAddress"]["poBox"] = po_box
        if "aptNumber" in subschema:
            schema["physicalAddress"]["aptNumber"] = subschema["aptNumber"]
        if "streetNumberName" in subschema:
            schema["physicalAddress"]["streetNumberName"] = subschema["streetNumberName"]

        master_list.append(schema)

    driver.quit()

    with open(
        os.path.join(ROOT_DIR, "scrapers", "virginia", "virginia.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list

if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
