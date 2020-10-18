import json
import os
import time
import shutil

import usaddress
from bs4 import BeautifulSoup as bS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://www.sos.mo.gov/elections/goVoteMissouri/localelectionauthority"
PATH_CHROMEDRIVER = shutil.which("chromedriver")


def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping

    boe_county = ["Clay", "Jackson", "Platte", "St. Louis"]
    boe_city = ["Kansas City", "St. Louis City"]

    if county_name in boe_county:
        location_name = f"{county_name} County Board of Elections"
    elif county_name in boe_city:
        location_name = f"{county_name} Board of Elections"
    elif county_name == "St. Charles":
        location_name = "St. Charles Country Election Authority"
    else:
        location_name = f"{county_name} County Election Office"

    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    final_address = {"locationName": location_name}

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]

    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]

    return final_address


def get_election_offices():
    # page is dynamic--use selenium to execute the javascript before extracting data
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options, executable_path=PATH_CHROMEDRIVER)
    driver.get(URL)
    time.sleep(1)

    soup = bS(driver.page_source, "html.parser")
    elems = soup.find_all(class_="group")

    master_list = []

    for e in elems:
        text = [i.strip() for i in e.get_text("\n").split("\n") if i.strip()]

        county = text[0].split(",")[0].split(" County")[0].split(" Board")[0]
        street_number_name = text[1]
        city = text[2].split(",")[0]
        zip_code = text[2].split()[-1]
        phone = text[3]
        website = URL if len(text) == 6 else text[-1]

        subschema = format_address_data(street_number_name, county)

        schema = {
            "countyName": county,
            "physicalAddress": {
                "city": city,
                "state": "Missouri",
                "zipCode": zip_code,
                "locationName": subschema["locationName"],
            },
            "phone": phone,
            "website": website,
        }

        if "poBox" in subschema:
            schema["physicalAddress"]["poBox"] = subschema["poBox"]
        if "aptNumber" in subschema:
            schema["physicalAddress"]["aptNumber"] = subschema["aptNumber"]
        if "streetNumberName" in subschema:
            schema["physicalAddress"]["streetNumberName"] = subschema[
                "streetNumberName"
            ]

        master_list.append(schema)

    with open(
        os.path.join(ROOT_DIR, "scrapers", "missouri", "missouri.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    print(ROOT_DIR)
    start = time.time()
    get_election_offices()
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
