import asyncio
import json
import os
import re
import time

import aiohttp
import usaddress
from bs4 import BeautifulSoup

from lib.ElectionSaver import electionsaver
from lib.definitions import Bcolors, ROOT_DIR

URL = "https://azsos.gov/county-election-info"


def find(string):
    # findall() has been used
    # with valid conditions for urls in string
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    return [x[0] for x in url]


def format_address_data(address, county_name):
    mapping = electionsaver.addressSchemaMapping

    parsed_data_dict = usaddress.tag(address, tag_mapping=mapping)[0]

    final_address = {
        "state": "Arizona",
        "zipCode": parsed_data_dict["zipCode"],
    }
    if "streetNumberName" in parsed_data_dict:
        final_address["streetNumberName"] = parsed_data_dict["streetNumberName"]
    if "city" in parsed_data_dict:
        final_address["city"] = parsed_data_dict["city"]
    if "poBox" in parsed_data_dict:
        final_address["poBox"] = parsed_data_dict["poBox"]
    final_address["locationName"] = parsed_data_dict.get(
        "locationName", f"{county_name} County Election Office"
    )
    if "aptNumber" in parsed_data_dict:
        final_address["aptNumber"] = parsed_data_dict["aptNumber"]
    return final_address


async def get_election_offices():
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as r:
            text = await r.read()
    soup = BeautifulSoup(text.decode("utf-8"), "html5lib")

    all_elems = soup.find_all("div", class_="nobs_body")

    county_names = []
    for i in soup.find_all("h2", class_="display-hide"):
        county_names.append(i.text.replace("County", ""))

    county_info_text = []

    for i in all_elems:
        county_info_text.append(i.text)

    county_info_text = county_info_text[:15]

    actual_info = []
    for i in county_info_text:
        actual_info.append(i.split("\n\n\t\t\t")[4])

    clerk_name = [i.split("\n\t\t\t\t")[0] for i in actual_info]
    building_name = [i.split("\n\t\t\t\t")[1] for i in actual_info]
    address_1 = [
        i.split("\n\t\t\t\t")[2].replace("Physical: ", "") for i in actual_info
    ]
    address_1 = [i.split(" (")[0] for i in address_1]
    address_2 = []
    for i in actual_info:
        if "Physical:" in i:
            addy = [i.split("\n\t\t\t\t")[4]]
        else:
            addy = [i.split("\n\t\t\t\t")[3]]
        address_2.append(addy)

    phone_num = []
    for i in county_info_text:
        phone = re.search("Phone - (.*)\n", i)
        phone_num.append(phone.group(1).split(" or")[0])

    flatten = lambda l: [item for sublist in l for item in sublist]

    address_2 = flatten(address_2)

    for n, i in enumerate(address_2):
        if i == "Phone - 520-724-4330":
            address_2[n] = ""
        if i == "Suite 101":
            address_2[n] = "Suite 101, Nogales, Arizona 85621"

    full_address = [a + ", " + b for a, b in zip(address_1, address_2)]

    websites = [find(i) for i in county_info_text]
    websites = [item for sublist in websites for item in sublist][::3]
    websites.remove("http://recorder.maricopa.gov/elections/")

    master_list = []

    for i in range(len(county_names)):
        address_schema = format_address_data(full_address[i], county_names[i])
        schema = {
            "countyName": county_names[i].strip(),
            "physicalAddress": address_schema,
            "phone": phone_num[i],
            "officeSupervisor": clerk_name[i],
            "supervisorTitle": building_name[i],
            "website": websites[i],
        }
        master_list.append(schema)

    with open(os.path.join(ROOT_DIR, "scrapers", "arizona", "arizona.json"), "w") as f:
        json.dump(master_list, f)
    return master_list


if __name__ == "__main__":
    start = time.time()
    asyncio.get_event_loop().run_until_complete(get_election_offices())
    end = time.time()
    print(f"{Bcolors.OKBLUE}Completed in {end - start} seconds.{Bcolors.ENDC}")
