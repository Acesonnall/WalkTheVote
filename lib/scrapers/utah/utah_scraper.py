import asyncio
import json
import os
import time

import aiohttp
import usaddress
from bs4 import BeautifulSoup as bS

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://elections.utah.gov/election-resources/county-clerks?__hstc=260729426.e5766c78049d793d1906ee81f9235fd6.1471824000059.1471824000061.1471824000062.2&__hssc=260729426.1.1471824000062&__hsfp=1773666937"


def format_address_data(address_data, county_name):
    mapping = electionsaver.addressSchemaMapping

    location_name = f"{county_name} County Election Office"

    # https://www.daggettcounty.org/16/ClerkTreasurer
    if county_name == 'Daggett':
        address_data = "95 North 1st West, P.O. Box 400"
    # http://sanjuancounty.org/index.php/clerkauditor/
    elif county_name == 'San Juan':
        address_data = "117 South Main, P.O. Box 338"

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

async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()

    soup = bS(text.decode("utf-8"), "html.parser")
    elems = soup.find_all("td")

    master_list = []

    for e in elems:
        text = [i.strip() for i in e.get_text('\n').split('\n') if i.strip()]
        if not text:
            continue

        county = text[0]
        clerk = text[1].split(":")[-1].strip()
        email = text[2] if county != "Daggett" else "Clerk-Treasurer@daggettcounty.org"
        street_number_name = text[3] if 'UT' in text[4] else f"{text[3]}, {text[4]}"
        city = text[-3].split(",")[0]
        zip_code = text[-3].split()[-1]
        phone = text[-2].split(":")[-1].strip()

        subschema = format_address_data(street_number_name, county)

        schema = {
            "countyName": county,
            "physicalAddress": {
                "city": city,
                "state": "Utah",
                "zipCode": zip_code,
                "locationName": subschema["locationName"],
            },
            "phone": phone,
            "email": email,
            "officeSupervisor": clerk,
            "website": URL,
        }

        if "poBox" in subschema:
            schema["physicalAddress"]["poBox"] = subschema["poBox"]
        if "aptNumber" in subschema:
            schema["physicalAddress"]["aptNumber"] = subschema["aptNumber"]
        if "streetNumberName" in subschema:
            schema["physicalAddress"]["streetNumberName"] = subschema["streetNumberName"]

        master_list.append(schema)

    with open(
        os.path.join(ROOT_DIR, "scrapers", "utah", "utah.json"), "w"
    ) as f:
        json.dump(master_list, f)
    return master_list


if __name__ =='__main__':
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
