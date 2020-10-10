import asyncio
import json
import os
import re
import time
from string import printable

import aiohttp
import usaddress
from bs4 import BeautifulSoup as bS

# emailRegex = re.search('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', cleanedData)
from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

BASE_URL = "https://sos.nebraska.gov/elections/election-officials-contact-information"


def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping

    location_name = f"{county_name} County Election Office"

    if county_name == "Banner":
        address_data = "204 State St, PO Box 67"
        location_name = "Banner County Courthouse"
    if county_name == "Box Butte":
        address_data = "515 Box Butte Avenue #203, PO Box 678"

    parsed_data_dict = usaddress.tag(address_data, tag_mapping=mapping)[0]

    final_address = {"locationName": location_name}

    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    else:
        if county_name == "Frontier":
            final_address["streetNumberName"] = "1 Wellington St"
    if "locationName" in parsed_data_dict:
        final_address["locationName"] = parsed_data_dict["locationName"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]

    return final_address


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(BASE_URL) as r:
            text = await r.read()
    soup = bS(text.decode("utf-8"), "html.parser")

    elems = soup.find_all(class_="col-sm-6")

    master_list = []

    for e in elems:
        cleaned_data = re.sub("[^{}]+".format(printable), "", e.text)

        # (.*) matches EVERYTHING between "Name: " and "Party"
        # the space is important
        name_regex = re.search("Name:(.*)Party Affiliation:", cleaned_data)
        name = "None" if name_regex is None else name_regex[1]
        names: str = name.strip()

        addy_regex = re.search("Address:(.*)City", cleaned_data)
        addy = "None" if addy_regex is None else addy_regex[1]
        street_number_name: str = addy.strip()

        city_regex = re.search("City:(.*)Zip", cleaned_data)
        cities = "None" if city_regex is None else city_regex[1]
        city: str = cities.strip()

        county_regex = re.search("County:(.*)Name:", cleaned_data)
        count = "None" if county_regex is None else county_regex[1]
        no_parens = count.split("(")[0]
        county: str = no_parens.strip()

        zip_regex = re.search("Code:(.*)Phone", cleaned_data)
        z = "None" if zip_regex is None else zip_regex[1]
        zip_code: str = z.strip()

        pho_regex = re.search("Number:(.*)Fax", cleaned_data)
        ph = "None" if pho_regex is None else pho_regex[1]
        phone: str = ph.strip()

        em_regex = re.search("Email Address: (.*)", cleaned_data)
        e = "None" if em_regex is None else em_regex[1]
        email: str = e.strip()

        if county != "None":
            subschema = format_address_data(street_number_name, county)
            schema = {
                "countyName": county,
                "physicalAddress": {
                    "city": city,
                    "state": "Nebraska",
                    "zipCode": zip_code,
                    "locationName": subschema["locationName"],
                },
                "phone": phone,
                "email": email,
                "officeSupervisor": names,
                "website": "https://sos.nebraska.gov/elections/election-officials"
                           "-contact"
                "-information",
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
        os.path.join(ROOT_DIR, "scrapers", "nebraska", "nebraska.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
